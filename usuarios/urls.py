from django.urls import path

from . import views

app_name = "usuarios"

urlpatterns = [
    path("cadastro/", views.cadastro_cidadao, name="cadastro"),
    path("minhas-solicitacoes/", views.minhas_solicitacoes, name="minhas_solicitacoes"),
]
