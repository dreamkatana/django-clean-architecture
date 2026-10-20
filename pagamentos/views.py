import json
from decimal import Decimal, InvalidOperation

from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .services import realizar_transferencia


def home_view(request: HttpRequest) -> JsonResponse:
    return JsonResponse(
        {
            "mensagem": "API de Pagamentos Django no ar!",
            "status": "ok",
            "endpoints": {
                "transferir": "/api/transferir/ (POST)",
                "admin": "/admin/",
            },
        }
    )


@csrf_exempt
@require_POST
def transferir_view(request: HttpRequest) -> JsonResponse:
    try:
        dados = json.loads(request.body)
        origem_id = int(dados["origem_id"])
        destino_id = int(dados["destino_id"])
        valor = Decimal(str(dados["valor"]))
    except (KeyError, json.JSONDecodeError, InvalidOperation, ValueError, TypeError):
        return JsonResponse({"erro": "Dados inválidos na requisição."}, status=400)

    try:
        conta_atualizada = realizar_transferencia(
            conta_origem_id=origem_id,
            conta_destino_id=destino_id,
            valor=valor,
        )
        return JsonResponse(
            {"status": "sucesso", "novo_saldo": str(conta_atualizada.saldo)},
            status=200,
        )
    except ValidationError as erro:
        mensagem = erro.message if hasattr(erro, "message") else str(erro.messages[0])
        return JsonResponse({"erro": mensagem}, status=400)
    except ObjectDoesNotExist:
        return JsonResponse({"erro": "Conta não encontrada."}, status=404)
