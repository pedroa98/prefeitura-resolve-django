from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods, require_safe

from .forms import AtendimentoForm
from .models import HistoricoAtendimento, Resposta, Solicitacao
from .permissoes import pode_atender, pode_usar_painel, solicitacoes_para_atendimento


class AtendimentoDesatualizado(Exception):
    pass


def registrar_atendimento(solicitacao, usuario, dados):
    if not pode_atender(usuario, solicitacao):
        raise PermissionDenied
    if dados["versao"] != solicitacao.atualizado_em.isoformat():
        raise AtendimentoDesatualizado

    mudou = (
        dados["status"] != solicitacao.status
        or dados["prioridade"] != solicitacao.prioridade
    )
    with transaction.atomic():
        atualizadas = Solicitacao.objects.filter(
            pk=solicitacao.pk,
            organizacao_id=solicitacao.organizacao_id,
            atualizado_em=solicitacao.atualizado_em,
            status=solicitacao.status,
            prioridade=solicitacao.prioridade,
        ).update(
            status=dados["status"],
            prioridade=dados["prioridade"],
            atualizado_em=timezone.now(),
        )
        if atualizadas != 1:
            raise AtendimentoDesatualizado

        if mudou:
            HistoricoAtendimento.objects.create(
                solicitacao=solicitacao,
                autor=usuario,
                status_anterior=solicitacao.status,
                status_novo=dados["status"],
                prioridade_anterior=solicitacao.prioridade,
                prioridade_nova=dados["prioridade"],
            )
        if dados["texto"]:
            Resposta.objects.create(
                solicitacao=solicitacao,
                autor=usuario,
                texto=dados["texto"],
                publica=dados["publica"],
            )


@never_cache
@login_required(login_url="solicitacoes:entrar")
@require_safe
def painel(request):
    if not pode_usar_painel(request.user):
        return render(request, "solicitacoes/sem_vinculo.html", status=403)

    solicitacoes = solicitacoes_para_atendimento(request.user).select_related(
        "organizacao", "categoria",
    ).order_by("-criado_em", "-pk")
    pagina = Paginator(solicitacoes, 20).get_page(request.GET.get("pagina"))
    return render(request, "solicitacoes/painel.html", {"pagina": pagina})


@never_cache
@login_required(login_url="solicitacoes:entrar")
@require_http_methods(["GET", "POST"])
def atender_solicitacao(request, protocolo):
    solicitacao = get_object_or_404(Solicitacao, protocolo=protocolo)
    if not pode_atender(request.user, solicitacao):
        raise Http404("Solicitação não encontrada.")

    form = AtendimentoForm(
        request.POST if request.method == "POST" else None,
        solicitacao=solicitacao,
    )
    if request.method == "POST" and form.is_valid():
        try:
            registrar_atendimento(solicitacao, request.user, form.cleaned_data)
        except AtendimentoDesatualizado:
            form.add_error(None,
                "Esta solicitação foi atualizada depois que você abriu a tela. "
                "Copie sua mensagem, abra o atendimento novamente e confira os dados."
            )
        else:
            return redirect("solicitacoes:detalhe", protocolo=solicitacao.protocolo)

    return render(request, "solicitacoes/atender.html", {
        "solicitacao": solicitacao,
        "form": form,
    })
