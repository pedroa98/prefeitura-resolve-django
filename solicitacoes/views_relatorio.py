from statistics import mean, median

from django.db.models import Count, Exists, OuterRef, Subquery
from django.shortcuts import render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_safe

from .forms_painel import FiltroRelatorioForm
from .models import Resposta, Solicitacao
from .permissoes import pode_ver_relatorio, solicitacoes_para_relatorio


def _barra(label, value, maximum):
    return {
        "label": label,
        "value": value,
        "percent": round(value * 100 / maximum) if maximum else 0,
    }


@never_cache
@require_safe
def relatorio(request):
    if not pode_ver_relatorio(request.user):
        return render(request, "solicitacoes/sem_vinculo.html", status=403)

    form = FiltroRelatorioForm(request.GET)
    filtros_validos = form.is_valid()
    solicitacoes = solicitacoes_para_relatorio(request.user)

    if filtros_validos:
        dados = form.cleaned_data
        if dados["data_inicial"]:
            solicitacoes = solicitacoes.filter(
                criado_em__date__gte=dados["data_inicial"]
            )
        if dados["data_final"]:
            solicitacoes = solicitacoes.filter(
                criado_em__date__lte=dados["data_final"]
            )
        if dados["categoria"]:
            solicitacoes = solicitacoes.filter(categoria=dados["categoria"])
        if dados["status"]:
            solicitacoes = solicitacoes.filter(status=dados["status"])
    else:
        # Filtro inválido não deve exibir um conjunto mais amplo de dados.
        solicitacoes = solicitacoes.none()

    respostas_publicas = Resposta.objects.filter(
        solicitacao_id=OuterRef("pk"),
        publica=True,
    )
    primeira_resposta = respostas_publicas.order_by(
        "criado_em", "pk"
    ).values("criado_em")[:1]

    registros = list(
        solicitacoes.annotate(
            tem_resposta_publica=Exists(respostas_publicas),
            primeira_resposta_em=Subquery(primeira_resposta),
        ).values(
            "criado_em",
            "status",
            "tem_resposta_publica",
            "primeira_resposta_em",
        )
    )

    total = len(registros)
    respondidas = sum(item["tem_resposta_publica"] for item in registros)
    sem_resposta = total - respondidas

    horas_resposta = [
        (item["primeira_resposta_em"] - item["criado_em"]).total_seconds() / 3600
        for item in registros
        if item["primeira_resposta_em"] is not None
    ]

    faixas = [
        ("Até 24 horas", 0),
        ("Mais de 1 até 3 dias", 0),
        ("Mais de 3 até 7 dias", 0),
        ("Mais de 7 dias", 0),
    ]
    for horas in horas_resposta:
        if horas <= 24:
            faixas[0] = (faixas[0][0], faixas[0][1] + 1)
        elif horas <= 72:
            faixas[1] = (faixas[1][0], faixas[1][1] + 1)
        elif horas <= 168:
            faixas[2] = (faixas[2][0], faixas[2][1] + 1)
        else:
            faixas[3] = (faixas[3][0], faixas[3][1] + 1)

    status_totais = {
        item["status"]: item["total"]
        for item in solicitacoes.values("status").annotate(total=Count("pk"))
    }
    status_barras = [
        _barra(label, status_totais.get(value, 0), total)
        for value, label in Solicitacao.Status.choices
    ]
    respostas_barras = [
        _barra("Com resposta pública", respondidas, total),
        _barra("Sem resposta pública", sem_resposta, total),
    ]
    tempos_barras = [
        _barra(label, quantidade, len(horas_resposta))
        for label, quantidade in faixas
    ]

    return render(request, "solicitacoes/relatorio.html", {
        "form": form,
        "filtros_validos": filtros_validos,
        "total": total,
        "respondidas": respondidas,
        "sem_resposta": sem_resposta,
        "percentual_respondidas": round(respondidas * 100 / total) if total else 0,
        "percentual_sem_resposta": round(sem_resposta * 100 / total) if total else 0,
        "media_horas": mean(horas_resposta) if horas_resposta else None,
        "mediana_horas": median(horas_resposta) if horas_resposta else None,
        "status_barras": status_barras,
        "respostas_barras": respostas_barras,
        "tempos_barras": tempos_barras,
    })
