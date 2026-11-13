from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from organizacoes.models import Organizacao
from solicitacoes.models import Categoria, Solicitacao

from .forms import CadastroCidadaoForm


class CadastroCidadaoFormTests(TestCase):
    def test_formulario_aceita_dados_validos(self):
        form = CadastroCidadaoForm(data={
            "username": "cidadao_teste",
            "email": "cidadao@example.com",
            "password1": "SenhaForte#2026",
            "password2": "SenhaForte#2026",
        })

        self.assertTrue(form.is_valid(), form.errors)

    def test_formulario_rejeita_senhas_diferentes(self):
        form = CadastroCidadaoForm(data={
            "username": "cidadao_teste",
            "email": "cidadao@example.com",
            "password1": "SenhaForte#2026",
            "password2": "OutraSenha#2026",
        })

        self.assertFalse(form.is_valid())
        self.assertIn("password2", form.errors)


class CadastroCidadaoViewTests(TestCase):
    def test_cadastro_cria_conta_e_inicia_sessao(self):
        resposta = self.client.post(
            reverse("usuarios:cadastro"),
            data={
                "username": "novo_cidadao",
                "email": "novo@example.com",
                "password1": "SenhaForte#2026",
                "password2": "SenhaForte#2026",
            },
        )

        usuario = get_user_model().objects.get(username="novo_cidadao")

        self.assertRedirects(
            resposta,
            reverse("usuarios:minhas_solicitacoes"),
        )
        self.assertTrue(usuario.is_active)
        self.assertFalse(usuario.is_staff)
        self.assertFalse(usuario.is_superuser)
        self.assertEqual(
            int(self.client.session["_auth_user_id"]),
            usuario.pk,
        )

    def test_cadastro_com_usuario_existente_mostra_erro(self):
        get_user_model().objects.create_user(
            username="usuario_existente",
            password="SenhaForte#2026",
        )

        resposta = self.client.post(
            reverse("usuarios:cadastro"),
            data={
                "username": "usuario_existente",
                "email": "outro@example.com",
                "password1": "SenhaForte#2026",
                "password2": "SenhaForte#2026",
            },
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertIn("username", resposta.context["form"].errors)
        self.assertEqual(
            get_user_model().objects.filter(
                username__iexact="usuario_existente"
            ).count(),
            1,
        )

    def test_usuario_autenticado_nao_acessa_tela_de_cadastro(self):
        usuario = get_user_model().objects.create_user(
            username="ja_cadastrado",
            password="SenhaForte#2026",
        )
        self.client.force_login(usuario)

        resposta = self.client.get(reverse("usuarios:cadastro"))

        self.assertRedirects(
            resposta,
            reverse("usuarios:minhas_solicitacoes"),
        )


class MinhasSolicitacoesTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.cidadao = User.objects.create_user(
            username="cidadao_um",
            password="SenhaForte#2026",
        )
        self.outro_cidadao = User.objects.create_user(
            username="cidadao_dois",
            password="SenhaForte#2026",
        )
        self.organizacao = Organizacao.objects.create(
            nome="Prefeitura de Teste",
            municipio="Recife",
            uf="PE",
        )
        self.categoria = Categoria.objects.create(nome="Iluminação")

    def criar_solicitacao(self, cidadao, titulo):
        return Solicitacao.objects.create(
            organizacao=self.organizacao,
            categoria=self.categoria,
            cidadao=cidadao,
            titulo=titulo,
            descricao="Descrição fictícia do problema.",
            bairro="Boa Vista",
            endereco="Rua de Teste",
        )

    def test_visitante_e_redirecionado_para_login(self):
        resposta = self.client.get(
            reverse("usuarios:minhas_solicitacoes")
        )

        self.assertRedirects(
            resposta,
            f"{reverse('solicitacoes:entrar')}?next="
            f"{reverse('usuarios:minhas_solicitacoes')}",
        )

    def test_cidadao_ve_somente_as_proprias_solicitacoes(self):
        propria = self.criar_solicitacao(
            self.cidadao,
            "Buraco perto de casa",
        )
        self.criar_solicitacao(
            self.outro_cidadao,
            "Lâmpada apagada",
        )

        self.client.force_login(self.cidadao)
        resposta = self.client.get(
            reverse("usuarios:minhas_solicitacoes")
        )

        self.assertEqual(resposta.status_code, 200)
        itens = resposta.context["pagina"].object_list
        self.assertEqual([item.pk for item in itens], [propria.pk])