from organizacoes.models import Vinculo


def pode_acessar(request, solicitacao):
    usuario = request.user

    if usuario.is_authenticated and usuario.is_active:
        if (
            usuario.is_superuser
            or solicitacao.cidadao_id == usuario.pk
        ):
            return True

        if Vinculo.objects.filter(
            usuario=usuario,
            organizacao=solicitacao.organizacao,
            ativo=True,
            organizacao__ativa=True,
            funcao__in=[
                Vinculo.Funcao.ADMINISTRADOR,
                Vinculo.Funcao.FUNCIONARIO,
            ],
        ).exists():
            return True

    acessos = request.session.get("acessos_anonimos", {})

    return (
        solicitacao.cidadao_id is None
        and bool(solicitacao.chave_acesso_hash)
        and acessos.get(str(solicitacao.protocolo))
        == solicitacao.chave_acesso_hash
    )


def liberar_acesso_anonimo(request, solicitacao):
    acessos = request.session.get(
        "acessos_anonimos", {}
    ).copy()

    acessos[str(solicitacao.protocolo)] = (
        solicitacao.chave_acesso_hash
    )

    request.session["acessos_anonimos"] = dict(
        list(acessos.items())[-20:]
    )