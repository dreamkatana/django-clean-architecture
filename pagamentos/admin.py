from django.contrib import admin

from .models import Conta


@admin.register(Conta)
class ContaAdmin(admin.ModelAdmin):
    list_display = ("titular", "saldo", "criado_em")
    search_fields = ("titular",)
