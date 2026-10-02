from django.contrib import admin

from .models import Categoria, Solicitacao


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("nome", "ativa")
    search_fields = ("nome",)
    list_filter = ("ativa",)


@admin.register(Solicitacao)
class SolicitacaoAdmin(admin.ModelAdmin):
    list_display = (
        "protocolo",
        "titulo",
        "organizacao",
        "categoria",
        "status",
        "prioridade",
        "criado_em",
    )

    list_filter = (
        "organizacao",
        "categoria",
        "status",
        "prioridade",
    )

    search_fields = (
        "protocolo",
        "titulo",
        "descricao",
        "cep",
        "bairro",
        "endereco",
        "ponto_referencia",
    )

    readonly_fields = (
        "protocolo",
        "criado_em",
        "atualizado_em",
    )

    def has_delete_permission(self, request, obj=None):
        return False