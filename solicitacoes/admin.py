from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import Categoria, HistoricoAtendimento, Resposta, Solicitacao


class ApenasAdminGeral(admin.ModelAdmin):
    def autorizado(self, request):
        return request.user.is_active and request.user.is_superuser

    def has_module_permission(self, request):
        return self.autorizado(request)

    def has_view_permission(self, request, obj=None):
        return self.autorizado(request)

    def has_add_permission(self, request):
        return self.autorizado(request)

    def has_change_permission(self, request, obj=None):
        return self.autorizado(request)

    def has_delete_permission(self, request, obj=None):
        return self.autorizado(request)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset if self.autorizado(request) else queryset.none()


@admin.register(Categoria)
class CategoriaAdmin(ApenasAdminGeral):
    list_display = ["nome", "ativa"]
    list_filter = ["ativa"]
    search_fields = ["nome", "descricao"]


@admin.register(Solicitacao)
class SolicitacaoAdmin(ApenasAdminGeral):
    list_display = [
        "protocolo", "titulo", "organizacao", "categoria",
        "status", "prioridade", "criado_em",
    ]
    list_filter = ["organizacao", "categoria", "status", "prioridade"]
    search_fields = [
        "protocolo", "titulo", "descricao", "cep", "bairro",
        "endereco", "ponto_referencia",
    ]
    readonly_fields = [
        "protocolo", "status", "prioridade", "criado_em",
        "atualizado_em", "abrir_atendimento",
    ]

    def get_readonly_fields(self, request, obj=None):
        campos = list(super().get_readonly_fields(request, obj))
        if obj is not None:
            campos += ["organizacao", "cidadao"]
        return campos

    @admin.display(description="Atendimento")
    def abrir_atendimento(self, obj):
        if not obj or not obj.pk:
            return "Salve a solicitação para abrir o atendimento."
        url = reverse("solicitacoes:atender", args=[obj.protocolo])
        return format_html('<a href="{}">Abrir tela de atendimento</a>', url)

    def save_model(self, request, obj, form, change):
        if change:
            # Salva apenas os campos editáveis alterados, preservando o atendimento.
            obj.save(update_fields=[*form.changed_data, "atualizado_em"])
        else:
            super().save_model(request, obj, form, change)

    def has_delete_permission(self, request, obj=None):
        return False


class RegistroSomenteLeitura(ApenasAdminGeral):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Resposta)
class RespostaAdmin(RegistroSomenteLeitura):
    list_display = ["solicitacao", "autor", "publica", "criado_em"]
    list_filter = ["publica"]
    search_fields = ["solicitacao__protocolo", "texto"]


@admin.register(HistoricoAtendimento)
class HistoricoAtendimentoAdmin(RegistroSomenteLeitura):
    list_display = [
        "solicitacao", "autor", "status_anterior", "status_novo",
        "prioridade_anterior", "prioridade_nova", "criado_em",
    ]
    search_fields = ["solicitacao__protocolo"]
