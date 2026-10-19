from decimal import Decimal

import pytest

from pagamentos.models import Conta


@pytest.mark.django_db
def test_conta_str_representation():
    conta = Conta.objects.create(titular="João Silva", saldo=Decimal("150.75"))
    assert str(conta) == "João Silva (€ 150.75)"
