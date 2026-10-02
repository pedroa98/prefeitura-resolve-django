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



def vinculos_atendimento(usuario):
    return Vinculo.objects.filter(
        usuario=usuario,
        ativo=True,
        organizacao__ativa=True,
        funcao__in=[Vinculo.Funcao.ADMINISTRADOR, Vinculo.Funcao.FUNCIONARIO],
    )


def pode_usar_painel(usuario):
    if not usuario.is_authenticated or not usuario.is_active:
        return False
    return usuario.is_superuser or vinculos_atendimento(usuario).exists()


def pode_atender(usuario, solicitacao):
    if not usuario.is_authenticated or not usuario.is_active:
        return False
    return usuario.is_superuser or vinculos_atendimento(usuario).filter(
        organizacao_id=solicitacao.organizacao_id,
    ).exists()


def solicitacoes_para_atendimento(usuario):
    from .models import Solicitacao

    if not usuario.is_authenticated or not usuario.is_active:
        return Solicitacao.objects.none()
    if usuario.is_superuser:
        return Solicitacao.objects.all()
    return Solicitacao.objects.filter(
        organizacao_id__in=vinculos_atendimento(usuario).values("organizacao_id"),
    )
