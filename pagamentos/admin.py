from django.contrib import admin

from .models import Conta, RegistroIdempotencia


@admin.register(Conta)
class ContaAdmin(admin.ModelAdmin):
    list_display = ("titular", "saldo", "criado_em")
    search_fields = ("titular",)


@admin.register(RegistroIdempotencia)
class RegistroIdempotenciaAdmin(admin.ModelAdmin):
    list_display = ("chave", "status_code", "criado_em")
    search_fields = ("chave",)
    readonly_fields = ("chave", "resultado", "status_code", "criado_em")
