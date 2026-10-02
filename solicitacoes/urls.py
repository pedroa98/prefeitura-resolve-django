from django.urls import path

from . import views

app_name = "solicitacoes"

urlpatterns = [
    path(
        "nova/",
        views.nova_solicitacao,
        name="nova",
    ),
    path(
        "consulta/",
        views.consultar_solicitacao,
        name="consulta",
    ),
    path(
        "solicitacao/<uuid:protocolo>/",
        views.detalhe_solicitacao,
        name="detalhe",
    ),
    path(
        "anexos/<path:arquivo>",
        views.imagem_solicitacao,
        name="imagem",
    ),
]