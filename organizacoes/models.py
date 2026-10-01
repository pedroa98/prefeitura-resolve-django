from django.conf import settings
from django.db import models


class Organizacao(models.Model):
    nome = models.CharField(max_length=150)
    municipio = models.CharField(max_length=100)
    uf = models.CharField(max_length=2)
    ativa = models.BooleanField(default=True)

    def __str__(self):
        return self.nome


class Vinculo(models.Model):
    class Funcao(models.TextChoices):
        ADMINISTRADOR = "administrador", "Administrador da prefeitura"
        FUNCIONARIO = "funcionario", "Funcionário"

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="vinculos",
    )
    organizacao = models.ForeignKey(
        Organizacao,
        on_delete=models.PROTECT,
        related_name="vinculos",
    )
    funcao = models.CharField(
        max_length=20,
        choices=Funcao.choices,
        default=Funcao.FUNCIONARIO,
    )
    ativo = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["usuario", "organizacao"],
                name="vinculo_unico_usuario_organizacao",
            )
        ]

    def __str__(self):
        return (
            f"{self.usuario} — {self.organizacao} "
            f"({self.get_funcao_display()})"
        )