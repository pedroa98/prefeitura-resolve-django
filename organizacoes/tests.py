from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase

from .models import Organizacao, Vinculo


class OrganizacaoTests(TestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create_user(
            username="funcionario_teste",
            password="SenhaForte#2026",
        )
        self.organizacao = Organizacao.objects.create(
            nome="Prefeitura de Teste",
            municipio="Recife",
            uf="PE",
        )

    def test_organizacao_tem_valores_iniciais_e_representacao(self):
        self.assertTrue(self.organizacao.ativa)
        self.assertEqual(str(self.organizacao), "Prefeitura de Teste")

    def test_vinculo_criado_tem_funcao_padrao_de_funcionario(self):
        vinculo = Vinculo.objects.create(
            usuario=self.usuario,
            organizacao=self.organizacao,
        )

        self.assertEqual(vinculo.funcao, Vinculo.Funcao.FUNCIONARIO)
        self.assertTrue(vinculo.ativo)
        self.assertIn("funcionario_teste", str(vinculo))

    def test_nao_permite_dois_vinculos_do_usuario_na_mesma_organizacao(self):
        Vinculo.objects.create(
            usuario=self.usuario,
            organizacao=self.organizacao,
        )

        with self.assertRaises(IntegrityError), transaction.atomic():
            Vinculo.objects.create(
                usuario=self.usuario,
                organizacao=self.organizacao,
            )