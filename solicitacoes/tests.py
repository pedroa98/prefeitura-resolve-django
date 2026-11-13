from io import BytesIO
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from PIL import Image

from organizacoes.models import Organizacao, Vinculo

from .forms import (
    AtendimentoForm,
    ConsultaSolicitacaoForm,
    EntrarForm,
    NovaSolicitacaoForm,
)
from .models import Categoria, HistoricoAtendimento, Resposta, Solicitacao


def imagem_jpeg():
    buffer = BytesIO()
    Image.new("RGB", (20, 20), color="red").save(buffer, format="JPEG")
    return SimpleUploadedFile(
        "teste.jpg",
        buffer.getvalue(),
        content_type="image/jpeg",
    )


class FormulariosSolicitacaoTests(TestCase):
    def setUp(self):
        self.organizacao = Organizacao.objects.create(
            nome="Prefeitura de Teste",
            municipio="Recife",
            uf="PE",
        )
        self.categoria = Categoria.objects.create(nome="Iluminação")

    def dados_solicitacao(self):
        return {
            "organizacao": self.organizacao.pk,
            "categoria": self.categoria.pk,
            "titulo": "Poste apagado",
            "descricao": "O poste está apagado há dois dias.",
            "cep": "50000-000",
            "bairro": "Boa Vista",
            "endereco": "Rua de Teste",
            "numero": "10",
            "ponto_referencia": "Perto da praça",
        }

    def test_formulario_de_solicitacao_valida_dados(self):
        form = NovaSolicitacaoForm(
            data=self.dados_solicitacao(),
            usuario=None,
        )

        self.assertTrue(form.is_valid(), form.errors)

    def test_formulario_rejeita_cep_invalido(self):
        dados = self.dados_solicitacao()
        dados["cep"] = "CEP errado"

        form = NovaSolicitacaoForm(data=dados, usuario=None)

        self.assertFalse(form.is_valid())
        self.assertIn("cep", form.errors)

    def test_formulario_exibe_placeholders_dos_campos(self):
        form = NovaSolicitacaoForm(usuario=None)

        self.assertTrue(form.fields["titulo"].widget.attrs["placeholder"])
        self.assertTrue(form.fields["descricao"].widget.attrs["placeholder"])
        self.assertTrue(form.fields["bairro"].widget.attrs["placeholder"])

    def test_formulario_anonimo_marca_campo_como_desabilitado(self):
        form = NovaSolicitacaoForm(usuario=None)

        self.assertTrue(form.fields["anonima"].disabled)
        self.assertTrue(form.fields["anonima"].initial)

    def test_formulario_processa_imagem_jpeg_valida(self):
        form = NovaSolicitacaoForm(
            data=self.dados_solicitacao(),
            files={"imagem": imagem_jpeg()},
            usuario=None,
        )

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(
            form.cleaned_data["imagem"].content_type,
            "image/jpeg",
        )

    def test_formulario_rejeita_arquivo_que_nao_e_imagem(self):
        arquivo = SimpleUploadedFile(
            "arquivo.jpg",
            b"isto nao e uma imagem",
            content_type="image/jpeg",
        )
        form = NovaSolicitacaoForm(
            data=self.dados_solicitacao(),
            files={"imagem": arquivo},
            usuario=None,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("imagem", form.errors)

    def test_formulario_de_consulta_rejeita_protocolo_invalido(self):
        form = ConsultaSolicitacaoForm(data={
            "protocolo": "nao-e-um-uuid",
            "chave": "chave-teste",
        })

        self.assertFalse(form.is_valid())
        self.assertIn("protocolo", form.errors)

    def test_formulario_de_login_tem_placeholders(self):
        form = EntrarForm()

        self.assertTrue(
            form.fields["username"].widget.attrs["placeholder"]
        )
        self.assertTrue(
            form.fields["password"].widget.attrs["placeholder"]
        )

    def test_formulario_de_atendimento_exige_mensagem_ao_encerrar(self):
        solicitacao = Solicitacao.objects.create(
            organizacao=self.organizacao,
            categoria=self.categoria,
            titulo="Poste apagado",
            descricao="Descrição de teste.",
            bairro="Boa Vista",
            endereco="Rua de Teste",
            status=Solicitacao.Status.ABERTA,
        )

        form = AtendimentoForm(
            data={
                "status": Solicitacao.Status.RESOLVIDA,
                "prioridade": Solicitacao.Prioridade.NORMAL,
                "texto": "",
                "publica": "",
                "versao": solicitacao.atualizado_em.isoformat(),
            },
            solicitacao=solicitacao,
        )

        self.assertFalse(form.is_valid())
        self.assertTrue(form.non_field_errors())


class SolicitacoesViewsTests(TestCase):
    def setUp(self):
        User = get_user_model()

        self.cidadao = User.objects.create_user(
            username="cidadao_teste",
            password="SenhaForte#2026",
        )
        self.outro_cidadao = User.objects.create_user(
            username="outro_teste",
            password="SenhaForte#2026",
        )
        self.funcionario = User.objects.create_user(
            username="funcionario_teste",
            password="SenhaForte#2026",
        )
        self.administrador = User.objects.create_user(
            username="admin_prefeitura",
            password="SenhaForte#2026",
        )

        self.organizacao = Organizacao.objects.create(
            nome="Prefeitura de Teste",
            municipio="Recife",
            uf="PE",
        )
        self.outra_organizacao = Organizacao.objects.create(
            nome="Outra Prefeitura",
            municipio="Olinda",
            uf="PE",
        )
        self.categoria = Categoria.objects.create(nome="Iluminação")

        Vinculo.objects.create(
            usuario=self.funcionario,
            organizacao=self.organizacao,
            funcao=Vinculo.Funcao.FUNCIONARIO,
        )
        Vinculo.objects.create(
            usuario=self.administrador,
            organizacao=self.organizacao,
            funcao=Vinculo.Funcao.ADMINISTRADOR,
        )

    def dados_solicitacao(self):
        return {
            "organizacao": self.organizacao.pk,
            "categoria": self.categoria.pk,
            "titulo": "Poste apagado",
            "descricao": "O poste está apagado há dois dias.",
            "cep": "50000-000",
            "bairro": "Boa Vista",
            "endereco": "Rua de Teste",
            "numero": "10",
            "ponto_referencia": "Perto da praça",
        }

    def criar_solicitacao(self, cidadao=None, **extras):
        dados = {
            "organizacao": self.organizacao,
            "categoria": self.categoria,
            "cidadao": cidadao,
            "titulo": "Solicitação de teste",
            "descricao": "Descrição fictícia.",
            "bairro": "Boa Vista",
            "endereco": "Rua de Teste",
        }
        dados.update(extras)
        return Solicitacao.objects.create(**dados)

    def obter_envio_id(self):
        resposta = self.client.get(reverse("solicitacoes:nova"))
        self.assertEqual(resposta.status_code, 200)
        return resposta.context["envio_id"]

    def enviar_solicitacao(self, dados=None, files=None):
        envio_id = self.obter_envio_id()
        payload = self.dados_solicitacao()

        if dados:
            payload.update(dados)

        payload["envio_id"] = envio_id
        payload.update(files or {})

        resposta = self.client.post(
            reverse("solicitacoes:nova"),
            data=payload,
        )
        return resposta, envio_id

    def test_pagina_inicial_abre(self):
        resposta = self.client.get(reverse("solicitacoes:inicio"))

        self.assertEqual(resposta.status_code, 200)

    def test_get_de_nova_solicitacao_exibe_formulario(self):
        resposta = self.client.get(reverse("solicitacoes:nova"))

        self.assertEqual(resposta.status_code, 200)
        self.assertIn("form", resposta.context)
        self.assertTrue(resposta.context["envio_id"])

    def test_envia_solicitacao_anonima_valida(self):
        resposta, _ = self.enviar_solicitacao()

        self.assertEqual(resposta.status_code, 200)
        self.assertTemplateUsed(
            resposta,
            "solicitacoes/comprovante.html",
        )

        solicitacao = Solicitacao.objects.get()
        self.assertIsNone(solicitacao.cidadao)
        self.assertTrue(solicitacao.chave_acesso_hash)
        self.assertTrue(resposta.context["chave"])

    def test_envia_solicitacao_anonima_com_imagem(self):
        resposta, _ = self.enviar_solicitacao(
            files={"imagem": imagem_jpeg()},
        )

        self.assertEqual(resposta.status_code, 200)

        solicitacao = Solicitacao.objects.get()
        self.assertTrue(solicitacao.imagem)
        self.assertTrue(
            solicitacao.imagem.storage.exists(solicitacao.imagem.name)
        )

        solicitacao.imagem.delete(save=False)

    def test_envia_solicitacao_com_conta(self):
        self.client.force_login(self.cidadao)
        resposta, _ = self.enviar_solicitacao()

        self.assertEqual(resposta.status_code, 200)

        solicitacao = Solicitacao.objects.get()
        self.assertEqual(solicitacao.cidadao, self.cidadao)
        self.assertFalse(solicitacao.chave_acesso_hash)

    def test_solicitacao_invalida_nao_e_salva(self):
        resposta, _ = self.enviar_solicitacao(
            dados={"titulo": ""},
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(Solicitacao.objects.count(), 0)
        self.assertIn("titulo", resposta.context["form"].errors)

    def test_formulario_expirado_nao_cria_solicitacao(self):
        self.client.get(reverse("solicitacoes:nova"))

        resposta = self.client.post(
            reverse("solicitacoes:nova"),
            data={
                **self.dados_solicitacao(),
                "envio_id": str(uuid4()),
            },
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(Solicitacao.objects.count(), 0)
        self.assertTrue(resposta.context["form"].non_field_errors())

    def test_mesmo_formulario_nao_registra_solicitacao_duas_vezes(self):
        resposta, envio_id = self.enviar_solicitacao()
        self.assertEqual(resposta.status_code, 200)

        resposta_repetida = self.client.post(
            reverse("solicitacoes:nova"),
            data={
                **self.dados_solicitacao(),
                "envio_id": envio_id,
            },
        )

        self.assertEqual(resposta_repetida.status_code, 200)
        self.assertEqual(Solicitacao.objects.count(), 1)

    def test_consulta_anonima_com_chave_correta_abre_solicitacao(self):
        solicitacao = self.criar_solicitacao(
            cidadao=None,
            chave_acesso_hash=make_password("chave-correta"),
        )

        resposta = self.client.post(
            reverse("solicitacoes:consulta"),
            data={
                "protocolo": solicitacao.protocolo,
                "chave": "chave-correta",
            },
        )

        self.assertRedirects(
            resposta,
            reverse(
                "solicitacoes:detalhe",
                kwargs={"protocolo": solicitacao.protocolo},
            ),
        )

    def test_consulta_anonima_com_chave_errada_nao_abre_solicitacao(self):
        solicitacao = self.criar_solicitacao(
            cidadao=None,
            chave_acesso_hash=make_password("chave-correta"),
        )

        resposta = self.client.post(
            reverse("solicitacoes:consulta"),
            data={
                "protocolo": solicitacao.protocolo,
                "chave": "chave-incorreta",
            },
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertTrue(resposta.context["form"].non_field_errors())

    def test_cidadao_autenticado_consulta_sua_solicitacao(self):
        solicitacao = self.criar_solicitacao(cidadao=self.cidadao)
        self.client.force_login(self.cidadao)

        resposta = self.client.post(
            reverse("solicitacoes:consulta"),
            data={
                "protocolo": solicitacao.protocolo,
                "chave": "",
            },
        )

        self.assertRedirects(
            resposta,
            reverse(
                "solicitacoes:detalhe",
                kwargs={"protocolo": solicitacao.protocolo},
            ),
        )

    def test_cidadao_nao_acessa_solicitacao_de_outra_conta(self):
        solicitacao = self.criar_solicitacao(
            cidadao=self.outro_cidadao,
        )
        self.client.force_login(self.cidadao)

        resposta = self.client.get(
            reverse(
                "solicitacoes:detalhe",
                kwargs={"protocolo": solicitacao.protocolo},
            )
        )

        self.assertEqual(resposta.status_code, 404)

    def test_funcionario_nao_acessa_solicitacao_de_outra_prefeitura(self):
        solicitacao = Solicitacao.objects.create(
            organizacao=self.outra_organizacao,
            categoria=self.categoria,
            titulo="Solicitação de outra prefeitura",
            descricao="Descrição fictícia.",
            bairro="Centro",
            endereco="Rua de Teste",
        )
        self.client.force_login(self.funcionario)

        resposta = self.client.get(
            reverse(
                "solicitacoes:detalhe",
                kwargs={"protocolo": solicitacao.protocolo},
            )
        )

        self.assertEqual(resposta.status_code, 404)

    def test_painel_exige_login(self):
        resposta = self.client.get(reverse("solicitacoes:painel"))

        self.assertRedirects(
            resposta,
            f"{reverse('solicitacoes:entrar')}?next="
            f"{reverse('solicitacoes:painel')}",
        )

    def test_funcionario_acessa_painel_da_propria_prefeitura(self):
        propria = self.criar_solicitacao(
            titulo="Da prefeitura vinculada",
        )
        outra = Solicitacao.objects.create(
            organizacao=self.outra_organizacao,
            categoria=self.categoria,
            titulo="De outra prefeitura",
            descricao="Descrição fictícia.",
            bairro="Centro",
            endereco="Rua de Teste",
        )
        self.client.force_login(self.funcionario)

        resposta = self.client.get(reverse("solicitacoes:painel"))
        itens = list(resposta.context["pagina"].object_list)

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual([item.pk for item in itens], [propria.pk])
        self.assertNotIn(outra, itens)

    def test_usuario_sem_vinculo_recebe_acesso_negado_no_painel(self):
        self.client.force_login(self.cidadao)

        resposta = self.client.get(reverse("solicitacoes:painel"))

        self.assertEqual(resposta.status_code, 403)

    def test_relatorio_so_e_acessivel_a_administrador_da_prefeitura(self):
        self.client.force_login(self.funcionario)
        resposta_funcionario = self.client.get(
            reverse("solicitacoes:relatorio")
        )
        self.assertEqual(resposta_funcionario.status_code, 403)

        self.client.force_login(self.administrador)
        resposta_administrador = self.client.get(
            reverse("solicitacoes:relatorio")
        )
        self.assertEqual(resposta_administrador.status_code, 200)

    def test_relatorio_calcula_solicitacoes_com_e_sem_resposta_publica(self):
        com_resposta = self.criar_solicitacao(titulo="Com resposta")
        self.criar_solicitacao(titulo="Sem resposta")

        Resposta.objects.create(
            solicitacao=com_resposta,
            autor=self.funcionario,
            texto="A equipe verificará o problema.",
            publica=True,
        )
        self.client.force_login(self.administrador)

        resposta = self.client.get(reverse("solicitacoes:relatorio"))

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.context["total"], 2)
        self.assertEqual(resposta.context["respondidas"], 1)
        self.assertEqual(resposta.context["sem_resposta"], 1)

    def test_atendimento_registra_status_historico_e_resposta(self):
        solicitacao = self.criar_solicitacao()
        self.client.force_login(self.funcionario)

        pagina = self.client.get(
            reverse(
                "solicitacoes:atender",
                kwargs={"protocolo": solicitacao.protocolo},
            )
        )
        versao = pagina.context["form"].initial["versao"]

        resposta = self.client.post(
            reverse(
                "solicitacoes:atender",
                kwargs={"protocolo": solicitacao.protocolo},
            ),
            data={
                "status": Solicitacao.Status.EM_ATENDIMENTO,
                "prioridade": Solicitacao.Prioridade.ALTA,
                "texto": "A equipe iniciou a análise.",
                "publica": "on",
                "versao": versao,
            },
        )

        solicitacao.refresh_from_db()

        self.assertRedirects(
            resposta,
            reverse(
                "solicitacoes:detalhe",
                kwargs={"protocolo": solicitacao.protocolo},
            ),
        )
        self.assertEqual(
            solicitacao.status,
            Solicitacao.Status.EM_ATENDIMENTO,
        )
        self.assertEqual(HistoricoAtendimento.objects.count(), 1)
        self.assertEqual(Resposta.objects.count(), 1)
        self.assertTrue(Resposta.objects.get().publica)

    def test_sair_encaminha_para_consulta(self):
        self.client.force_login(self.cidadao)

        resposta = self.client.post(reverse("solicitacoes:sair"))

        self.assertRedirects(
            resposta,
            reverse("solicitacoes:consulta"),
        )