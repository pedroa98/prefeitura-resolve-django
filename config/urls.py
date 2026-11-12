from django.contrib import admin
from django.urls import include, path

from solicitacoes.forms import EntrarAdminForm

admin.site.login_form = EntrarAdminForm

urlpatterns = [
    path("admin/", admin.site.urls),
    path("conta/", include("usuarios.urls")),
    path("", include("solicitacoes.urls")),
]
