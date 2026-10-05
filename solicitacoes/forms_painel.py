from django import forms

from .models import Categoria, Solicitacao


class FiltroPainelForm(forms.Form):
    q = forms.CharField(
        label="Busca por título ou protocolo",
        required=False,
        max_length=150,
        help_text="Digite parte do título ou o protocolo completo.",
        widget=forms.TextInput(attrs={"type": "search"}),
    )
    status = forms.ChoiceField(
        label="Status",
        required=False,
        choices=[("", "Todos os status"), *Solicitacao.Status.choices],
    )
    categoria = forms.ModelChoiceField(
        label="Categoria",
        required=False,
        # Inclui categorias inativas para encontrar solicitações antigas.
        queryset=Categoria.objects.order_by("nome"),
        empty_label="Todas as categorias",
    )
    prioridade = forms.ChoiceField(
        label="Prioridade",
        required=False,
        choices=[("", "Todas as prioridades"), *Solicitacao.Prioridade.choices],
    )
