from io import BytesIO

from django import forms
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.validators import FileExtensionValidator
from PIL import Image, ImageOps

from organizacoes.models import Organizacao

from .models import Categoria, Solicitacao, validar_tamanho_imagem


class NovaSolicitacaoForm(forms.ModelForm):
    anonima = forms.BooleanField(
        label="Enviar anonimamente",
        required=False,
    )

    class Meta:
        model = Solicitacao
        fields = [
            "organizacao",
            "categoria",
            "titulo",
            "descricao",
            "cep",
            "bairro",
            "endereco",
            "numero",
            "ponto_referencia",
            "imagem",
            "anonima",
        ]

    def __init__(self, *args, usuario=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["organizacao"].queryset = (
            Organizacao.objects.filter(ativa=True)
        )
        self.fields["categoria"].queryset = (
            Categoria.objects.filter(ativa=True)
        )
        self.fields["imagem"].help_text = (
            "JPG, PNG ou WebP, até 5 MB e 30 megapixels."
        )

        if usuario is None or not usuario.is_authenticated:
            self.fields["anonima"].initial = True
            self.fields["anonima"].disabled = True

    def clean_imagem(self):
        arquivo = self.cleaned_data.get("imagem")
        if not arquivo:
            return arquivo

        validar_tamanho_imagem(arquivo)
        FileExtensionValidator(
            ["jpg", "jpeg", "png", "webp"]
        )(arquivo)

        try:
            arquivo.seek(0)

            with Image.open(arquivo) as original:
                if original.format not in ["JPEG", "PNG", "WEBP"]:
                    raise forms.ValidationError(
                        "Envie uma imagem JPG, PNG ou WebP."
                    )

                if original.width * original.height > 30_000_000:
                    raise forms.ValidationError(
                        "Reduza a resolução para até 30 megapixels."
                    )

                imagem = ImageOps.exif_transpose(original)
                imagem.thumbnail((1920, 1920))

                rgba = imagem.convert("RGBA")
                limpa = Image.new("RGB", rgba.size, "white")
                limpa.paste(rgba, mask=rgba.getchannel("A"))

                resultado = BytesIO()
                limpa.save(resultado, format="JPEG", quality=85)

        except (
            OSError,
            ValueError,
            Image.DecompressionBombError,
        ) as erro:
            raise forms.ValidationError(
                "Não foi possível processar a imagem."
            ) from erro

        return SimpleUploadedFile(
            "imagem.jpg",
            resultado.getvalue(),
            content_type="image/jpeg",
        )


class ConsultaSolicitacaoForm(forms.Form):
    protocolo = forms.UUIDField(label="Protocolo")

    chave = forms.CharField(
        label="Chave de acesso",
        max_length=64,
        required=False,
        widget=forms.PasswordInput(
            attrs={"autocomplete": "off"}
        ),
        help_text=(
            "Obrigatória para consultar uma solicitação anônima."
        ),
    )