from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from pagamentos.models import Conta
from pagamentos.services import realizar_transferencia


@pytest.mark.django_db
def test_deve_transferir_saldo_entre_contas_com_sucesso():
    # Arrange (Dado que existem duas contas)
    origem = Conta.objects.create(titular="João", saldo=Decimal("100.00"))
    destino = Conta.objects.create(titular="Maria", saldo=Decimal("50.00"))

    # Act (Quando realizo a transferência)
    realizar_transferencia(
        conta_origem_id=origem.id,
        conta_destino_id=destino.id,
        valor=Decimal("30.00"),
    )

    # Assert (Então os saldos são atualizados no banco)
    origem.refresh_from_db()
    destino.refresh_from_db()
    assert origem.saldo == Decimal("70.00")
    assert destino.saldo == Decimal("80.00")


@pytest.mark.django_db
def test_deve_bloquear_transferencia_sem_saldo():
    # Arrange
    origem = Conta.objects.create(titular="João", saldo=Decimal("10.00"))
    destino = Conta.objects.create(titular="Maria", saldo=Decimal("50.00"))

    # Act & Assert
    with pytest.raises(ValidationError, match="Saldo insuficiente."):
        realizar_transferencia(
            conta_origem_id=origem.id,
            conta_destino_id=destino.id,
            valor=Decimal("50.00"),
        )


@pytest.mark.django_db
def test_deve_bloquear_transferencia_com_valor_invalido():
    origem = Conta.objects.create(titular="João", saldo=Decimal("100.00"))
    destino = Conta.objects.create(titular="Maria", saldo=Decimal("50.00"))

    with pytest.raises(ValidationError, match="O valor da transferência deve ser positivo."):
        realizar_transferencia(
            conta_origem_id=origem.id,
            conta_destino_id=destino.id,
            valor=Decimal("0.00"),
        )

    with pytest.raises(ValidationError, match="O valor da transferência deve ser positivo."):
        realizar_transferencia(
            conta_origem_id=origem.id,
            conta_destino_id=destino.id,
            valor=Decimal("-15.00"),
        )


@pytest.mark.django_db
def test_deve_bloquear_transferencia_para_mesma_conta():
    origem = Conta.objects.create(titular="João", saldo=Decimal("100.00"))

    with pytest.raises(ValidationError, match="A conta de origem e destino não podem ser iguais."):
        realizar_transferencia(
            conta_origem_id=origem.id,
            conta_destino_id=origem.id,
            valor=Decimal("20.00"),
        )


@pytest.mark.django_db
def test_deve_respeitar_idempotencia_ao_chamar_servico_diretamente():
    origem = Conta.objects.create(titular="João", saldo=Decimal("100.00"))
    destino = Conta.objects.create(titular="Maria", saldo=Decimal("50.00"))

    realizar_transferencia(
        conta_origem_id=origem.id,
        conta_destino_id=destino.id,
        valor=Decimal("30.00"),
        chave_idempotencia="service-key-123",
    )
    # Chamada repetida com a mesma chave não debita novamente
    realizar_transferencia(
        conta_origem_id=origem.id,
        conta_destino_id=destino.id,
        valor=Decimal("30.00"),
        chave_idempotencia="service-key-123",
    )

    origem.refresh_from_db()
    destino.refresh_from_db()
    assert origem.saldo == Decimal("70.00")
    assert destino.saldo == Decimal("80.00")
