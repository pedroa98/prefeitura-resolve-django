from django.contrib import admin

from .models import Organizacao, Vinculo


@admin.register(Organizacao)
class OrganizacaoAdmin(admin.ModelAdmin):
    list_display = ("nome", "municipio", "uf", "ativa")
    search_fields = ("nome", "municipio")
    list_filter = ("uf", "ativa")


@admin.register(Vinculo)
class VinculoAdmin(admin.ModelAdmin):
    list_display = ("usuario", "organizacao", "funcao", "ativo")
    list_filter = ("organizacao", "funcao", "ativo")
    search_fields = ("usuario__username", "organizacao__nome")