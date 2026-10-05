from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
from django.shortcuts import redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods, require_safe
from django.views.decorators.debug import sensitive_post_parameters

from solicitacoes.models import Solicitacao

from .forms import CadastroCidadaoForm


@never_cache
@sensitive_post_parameters("password1", "password2")
@require_http_methods(["GET", "POST"])
def cadastro_cidadao(request):
    if request.user.is_authenticated:
        return redirect("usuarios:minhas_solicitacoes")

    form = CadastroCidadaoForm(
        request.POST if request.method == "POST" else None,
    )
    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                usuario = form.save(commit=False)
                usuario.is_staff = False
                usuario.is_superuser = False
                usuario.is_active = True
                usuario.save()
        except IntegrityError:
            if not get_user_model().objects.filter(
                username__iexact=form.cleaned_data["username"],
            ).exists():
                raise
            form.add_error("username", "Este nome de usuário já está em uso.")
        else:
            login(request, usuario)
            return redirect("usuarios:minhas_solicitacoes")

    return render(request, "usuarios/cadastro.html", {"form": form})


@never_cache
@login_required(login_url="solicitacoes:entrar")
@require_safe
def minhas_solicitacoes(request):
    solicitacoes = Solicitacao.objects.filter(
        cidadao=request.user,
    ).select_related("organizacao", "categoria").order_by("-criado_em", "-pk")
    pagina = Paginator(solicitacoes, 20).get_page(request.GET.get("pagina"))
    return render(request, "usuarios/minhas_solicitacoes.html", {"pagina": pagina})
