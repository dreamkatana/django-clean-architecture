from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from .models import Conta


@transaction.atomic  # Garante rollback automático se algo der erro
def realizar_transferencia(*, conta_origem_id: int, conta_destino_id: int, valor: Decimal) -> Conta:
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

    return origem
