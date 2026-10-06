from django.shortcuts import render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_safe

from .permissoes import pode_usar_painel


@never_cache
@require_safe
def inicio(request):
    return render(request, "solicitacoes/inicio.html", {
        "area_equipe": pode_usar_painel(request.user),
    })
