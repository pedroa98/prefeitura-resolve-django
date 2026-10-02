import secrets
import uuid

from django.contrib.auth.hashers import (
    check_password,
    make_password,
)
from django.db import IntegrityError, transaction
from django.http import FileResponse, Http404
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.views.decorators.cache import never_cache
from django.views.decorators.http import (
    require_http_methods,
    require_safe,
)

from .forms import (
    ConsultaSolicitacaoForm,
    NovaSolicitacaoForm,
)
from .models import Solicitacao
from .permissoes import (
    liberar_acesso_anonimo,
    pode_acessar,
)


@never_cache
@require_http_methods(["GET", "POST"])
def nova_solicitacao(request):
    if request.method == "GET":
        request.session.setdefault(
            "novo_envio",
            str(uuid.uuid4()),
        )
        form = NovaSolicitacaoForm(usuario=request.user)

    else:
        form = NovaSolicitacaoForm(
            request.POST,
            request.FILES,
            usuario=request.user,
        )
        envio_id = request.session.get("novo_envio")

        if (
            not envio_id
            or request.POST.get("envio_id") != envio_id
        ):
            form.add_error(
                None,
                "Este formulário já foi enviado ou expirou. "
                "Abra um novo formulário.",
            )

        elif form.is_valid():
            solicitacao = form.save(commit=False)
            solicitacao.protocolo = uuid.UUID(envio_id)

            anonima = (
                form.cleaned_data["anonima"]
                or not request.user.is_authenticated
            )
            chave = None

            if anonima:
                solicitacao.cidadao = None
                chave = secrets.token_urlsafe(16)
                solicitacao.chave_acesso_hash = (
                    make_password(chave)
                )
            else:
                solicitacao.cidadao = request.user

            try:
                with transaction.atomic():
                    solicitacao.save()

            except IntegrityError:
                if (
                    solicitacao.imagem
                    and solicitacao.imagem._committed
                ):
                    solicitacao.imagem.delete(save=False)

                if not Solicitacao.objects.filter(
                    protocolo=solicitacao.protocolo
                ).exists():
                    raise

                form.add_error(
                    None,
                    "Este envio já foi registrado. "
                    "Consulte com os códigos recebidos.",
                )

            else:
                request.session.pop("novo_envio", None)

                if anonima:
                    liberar_acesso_anonimo(
                        request, solicitacao
                    )

                return render(
                    request,
                    "solicitacoes/comprovante.html",
                    {
                        "solicitacao": solicitacao,
                        "chave": chave,
                    },
                )

    return render(
        request,
        "solicitacoes/nova.html",
        {
            "form": form,
            "envio_id": request.session.get(
                "novo_envio", ""
            ),
        },
    )


@never_cache
@require_http_methods(["GET", "POST"])
def consultar_solicitacao(request):
    form = ConsultaSolicitacaoForm(
        request.POST if request.method == "POST" else None
    )

    if request.method == "POST" and form.is_valid():
        solicitacao = Solicitacao.objects.filter(
            protocolo=form.cleaned_data["protocolo"]
        ).first()
        chave = form.cleaned_data["chave"]

        if solicitacao:
            if pode_acessar(request, solicitacao):
                return redirect(
                    "solicitacoes:detalhe",
                    protocolo=solicitacao.protocolo,
                )

            if (
                solicitacao.cidadao_id is None
                and solicitacao.chave_acesso_hash
                and chave
                and check_password(
                    chave,
                    solicitacao.chave_acesso_hash,
                )
            ):
                liberar_acesso_anonimo(
                    request, solicitacao
                )
                return redirect(
                    "solicitacoes:detalhe",
                    protocolo=solicitacao.protocolo,
                )

        form.add_error(
            None,
            "Confira o protocolo, a chave "
            "ou o acesso da sua conta.",
        )

    return render(
        request,
        "solicitacoes/consulta.html",
        {"form": form},
    )


@never_cache
@require_safe
def detalhe_solicitacao(request, protocolo):
    from .permissoes import pode_atender

    solicitacao = get_object_or_404(Solicitacao, protocolo=protocolo)
    if not pode_acessar(request, solicitacao):
        raise Http404("Solicitação não encontrada.")

    equipe = pode_atender(request.user, solicitacao)
    respostas = solicitacao.respostas.select_related("autor")
    if not equipe:
        respostas = respostas.filter(publica=True)

    return render(request, "solicitacoes/detalhe.html", {
        "solicitacao": solicitacao,
        "equipe": equipe,
        "respostas": respostas,
        "historico": solicitacao.historico.select_related("autor"),
    })



@never_cache
@require_safe
def imagem_solicitacao(request, arquivo):
    solicitacao = get_object_or_404(
        Solicitacao,
        imagem=arquivo,
    )

    if not pode_acessar(request, solicitacao):
        raise Http404("Imagem não encontrada.")

    try:
        imagem = solicitacao.imagem.open("rb")
    except FileNotFoundError as erro:
        raise Http404(
            "Imagem não encontrada."
        ) from erro

    resposta = FileResponse(imagem)
    resposta["Cache-Control"] = "private, no-store"
    resposta["X-Content-Type-Options"] = "nosniff"

    return resposta