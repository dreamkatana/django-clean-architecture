from decimal import Decimal

import pytest

from pagamentos.models import Conta, RegistroIdempotencia


@pytest.mark.django_db
def test_conta_str_representation():
    conta = Conta.objects.create(titular="João Silva", saldo=Decimal("150.75"))
    assert str(conta) == "João Silva (€ 150.75)"


@pytest.mark.django_db
def test_registro_idempotencia_str():
    registro = RegistroIdempotencia.objects.create(
        chave="tx-test-999",
        resultado={"status": "sucesso"},
        status_code=200,
    )
    assert str(registro) == "Idempotencia tx-test-999 (200)"
