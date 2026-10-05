from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("conta/", include("usuarios.urls")),
    path("", include("solicitacoes.urls")),
]
