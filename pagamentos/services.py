from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from .models import Conta, RegistroIdempotencia


def obter_registro_idempotencia(chave: str) -> RegistroIdempotencia | None:
    return RegistroIdempotencia.objects.filter(chave=chave).first()


@transaction.atomic  # Garante rollback automático se algo der erro
def realizar_transferencia(
    *,
    conta_origem_id: int,
    conta_destino_id: int,
    valor: Decimal,
    chave_idempotencia: str | None = None,
) -> Conta:
    # Se a chave de idempotência já foi processada, retorna a conta sem reexecutar mutação
    if chave_idempotencia:
        registro = obter_registro_idempotencia(chave_idempotencia)
        if registro:
            return Conta.objects.get(id=conta_origem_id)

    if valor <= Decimal("0.00"):
        raise ValidationError("O valor da transferência deve ser positivo.")

    if conta_origem_id == conta_destino_id:
        raise ValidationError("A conta de origem e destino não podem ser iguais.")

    # select_for_update() trava as linhas no banco até o fim da transação (evita Race Condition)
    origem = Conta.objects.select_for_update().get(id=conta_origem_id)
    destino = Conta.objects.select_for_update().get(id=conta_destino_id)

    if origem.saldo < valor:
        raise ValidationError("Saldo insuficiente.")

    origem.saldo -= valor
    destino.saldo += valor

    origem.save(update_fields=["saldo"])
    destino.save(update_fields=["saldo"])

    if chave_idempotencia:
        RegistroIdempotencia.objects.create(
            chave=chave_idempotencia,
            resultado={"status": "sucesso", "novo_saldo": str(origem.saldo)},
            status_code=200,
        )

    return origem
