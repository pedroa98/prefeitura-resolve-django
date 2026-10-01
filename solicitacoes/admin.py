from django.contrib import admin

from .models import Categoria


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("nome", "ativa")
    search_fields = ("nome",)
    list_filter = ("ativa",)