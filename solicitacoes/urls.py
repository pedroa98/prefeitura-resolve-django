from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from . import views, views_atendimento

app_name = "solicitacoes"

urlpatterns = [
    path("nova/", views.nova_solicitacao, name="nova"),
    path("consulta/", views.consultar_solicitacao, name="consulta"),
    path("solicitacao/<uuid:protocolo>/", views.detalhe_solicitacao, name="detalhe"),
    path("anexos/<path:arquivo>", views.imagem_solicitacao, name="imagem"),
    path("painel/", views_atendimento.painel, name="painel"),
    path(
        "solicitacao/<uuid:protocolo>/atender/",
        views_atendimento.atender_solicitacao,
        name="atender",
    ),
    path(
        "entrar/",
        LoginView.as_view(
            template_name="solicitacoes/entrar.html",
            next_page="solicitacoes:consulta",
        ),
        name="entrar",
    ),
    path(
        "sair/",
        LogoutView.as_view(next_page="solicitacoes:consulta"),
        name="sair",
    ),
]
