import json
from decimal import Decimal

import pytest
from django.test import Client
from django.urls import reverse

from pagamentos.models import Conta


@pytest.mark.django_db
def test_transferir_view_sucesso(client: Client):
    origem = Conta.objects.create(titular="Carlos", saldo=Decimal("200.00"))
    destino = Conta.objects.create(titular="Ana", saldo=Decimal("50.00"))

    payload = {
        "origem_id": origem.id,
        "destino_id": destino.id,
        "valor": "75.50",
    }
    response = client.post(
        reverse("pagamentos:transferir"),
        data=json.dumps(payload),
        content_type="application/json",
    )

    assert response.status_code == 200
    dados = response.json()
    assert dados["status"] == "sucesso"
    assert dados["novo_saldo"] == "124.50"

    origem.refresh_from_db()
    destino.refresh_from_db()
    assert origem.saldo == Decimal("124.50")
    assert destino.saldo == Decimal("125.50")


@pytest.mark.django_db
def test_transferir_view_saldo_insuficiente(client: Client):
    origem = Conta.objects.create(titular="Carlos", saldo=Decimal("10.00"))
    destino = Conta.objects.create(titular="Ana", saldo=Decimal("50.00"))

    payload = {
        "origem_id": origem.id,
        "destino_id": destino.id,
        "valor": "100.00",
    }
    response = client.post(
        reverse("pagamentos:transferir"),
        data=json.dumps(payload),
        content_type="application/json",
    )

    assert response.status_code == 400
    dados = response.json()
    assert dados["erro"] == "Saldo insuficiente."


@pytest.mark.django_db
def test_transferir_view_conta_nao_encontrada(client: Client):
    origem = Conta.objects.create(titular="Carlos", saldo=Decimal("100.00"))

    payload = {
        "origem_id": origem.id,
        "destino_id": 99999,
        "valor": "50.00",
    }
    response = client.post(
        reverse("pagamentos:transferir"),
        data=json.dumps(payload),
        content_type="application/json",
    )

    assert response.status_code == 404
    dados = response.json()
    assert dados["erro"] == "Conta não encontrada."


@pytest.mark.django_db
def test_transferir_view_payload_invalido(client: Client):
    response = client.post(
        reverse("pagamentos:transferir"),
        data="invalid json",
        content_type="application/json",
    )
    assert response.status_code == 400
    dados = response.json()
    assert dados["erro"] == "Dados inválidos na requisição."


@pytest.mark.django_db
def test_transferir_view_metodo_get_nao_permitido(client: Client):
    response = client.get(reverse("pagamentos:transferir"))
    assert response.status_code == 405


@pytest.mark.django_db
def test_home_view_sucesso(client: Client):
    response = client.get(reverse("pagamentos:home"))
    assert response.status_code == 200
    dados = response.json()
    assert dados["status"] == "ok"
    assert "transferir" in dados["endpoints"]


@pytest.mark.django_db
def test_transferir_view_com_chave_idempotencia_nao_duplica_debito(client: Client):
    origem = Conta.objects.create(titular="Carlos", saldo=Decimal("100.00"))
    destino = Conta.objects.create(titular="Ana", saldo=Decimal("50.00"))

    payload = {
        "origem_id": origem.id,
        "destino_id": destino.id,
        "valor": "30.00",
    }
    idempotency_headers = {"HTTP_IDEMPOTENCY_KEY": "tx-key-abc-123"}

    # 1ª tentativa
    resp1 = client.post(
        reverse("pagamentos:transferir"),
        data=json.dumps(payload),
        content_type="application/json",
        **idempotency_headers,
    )
    assert resp1.status_code == 200
    assert resp1.json()["novo_saldo"] == "70.00"

    # 2ª tentativa com a mesma chave (ex: retry de rede)
    resp2 = client.post(
        reverse("pagamentos:transferir"),
        data=json.dumps(payload),
        content_type="application/json",
        **idempotency_headers,
    )
    assert resp2.status_code == 200
    assert resp2.json()["novo_saldo"] == "70.00"

    # Asserção crítica: o saldo no banco só foi debitado UMA vez!
    origem.refresh_from_db()
    destino.refresh_from_db()
    assert origem.saldo == Decimal("70.00")
    assert destino.saldo == Decimal("80.00")
