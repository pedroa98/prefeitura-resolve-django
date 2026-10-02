import uuid
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator, RegexValidator
from django.db import models


def validar_tamanho_imagem(arquivo):
    limite = 5 * 1024 * 1024

    if arquivo.size > limite:
        raise ValidationError("A imagem deve ter no máximo 5 MB.")


def caminho_imagem(instance, nome_original):
    extensao = Path(nome_original).suffix.lower()
    nome_arquivo = f"{uuid.uuid4().hex}{extensao}"

    return f"solicitacoes/{instance.protocolo}/{nome_arquivo}"


class Categoria(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    descricao = models.TextField(blank=True)
    ativa = models.BooleanField(default=True)

    class Meta:
        ordering = ["nome"]
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"

    def __str__(self):
        return self.nome


class Solicitacao(models.Model):
    class Status(models.TextChoices):
        ABERTA = "aberta", "Aberta"
        EM_ANALISE = "em_analise", "Em análise"
        EM_ATENDIMENTO = "em_atendimento", "Em atendimento"
        RESOLVIDA = "resolvida", "Resolvida"
        CANCELADA = "cancelada", "Cancelada"

    class Prioridade(models.TextChoices):
        BAIXA = "baixa", "Baixa"
        NORMAL = "normal", "Normal"
        ALTA = "alta", "Alta"
        URGENTE = "urgente", "Urgente"

    protocolo = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )

    organizacao = models.ForeignKey(
        "organizacoes.Organizacao",
        on_delete=models.PROTECT,
        related_name="solicitacoes",
    )

    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        related_name="solicitacoes",
    )

    cidadao = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="solicitacoes",
        null=True,
        blank=True,
        verbose_name="Cidadão",
    )

    titulo = models.CharField(
        max_length=150,
        verbose_name="Título",
    )
    descricao = models.TextField(verbose_name="Descrição")

    cep = models.CharField(
        max_length=9,
        blank=True,
        verbose_name="CEP do problema",
        validators=[
            RegexValidator(
                regex=r"^[0-9]{5}-?[0-9]{3}$",
                message="Informe o CEP como 12345678 ou 12345-678.",
            )
        ],
    )

    bairro = models.CharField(max_length=100)

    endereco = models.CharField(
        max_length=255,
        verbose_name="Rua ou avenida",
    )

    numero = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Número",
    )

    ponto_referencia = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Ponto de referência",
    )

    imagem = models.ImageField(
        upload_to=caminho_imagem,
        max_length=255,
        blank=True,
        verbose_name="Imagem do problema",
        validators=[
            FileExtensionValidator(
                allowed_extensions=["jpg", "jpeg", "png", "webp"]
            ),
            validar_tamanho_imagem,
        ],
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ABERTA,
    )

    prioridade = models.CharField(
        max_length=10,
        choices=Prioridade.choices,
        default=Prioridade.NORMAL,
    )

    chave_acesso_hash = models.CharField(
        max_length=128,
        blank=True,
        editable=False,
    )

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-criado_em"]
        verbose_name = "Solicitação"
        verbose_name_plural = "Solicitações"

    def __str__(self):
        return f"{self.protocolo} — {self.titulo}"