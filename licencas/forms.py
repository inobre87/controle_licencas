from django import forms
from django.core.exceptions import ValidationError

from .models import Fornecedor, CompraNF, Produto, Departamento, Licenca, LicencaUso


class FornecedorForm(forms.ModelForm):
    class Meta:
        model = Fornecedor
        fields = "__all__"


class CompraNFForm(forms.ModelForm):
    class Meta:
        model = CompraNF
        fields = "__all__"


class ProdutoForm(forms.ModelForm):
    class Meta:
        model = Produto
        fields = "__all__"


class DepartamentoForm(forms.ModelForm):
    class Meta:
        model = Departamento
        fields = "__all__"


class LicencaForm(forms.ModelForm):
    class Meta:
        model = Licenca
        fields = "__all__"

    def clean_chave_serial(self):
        chave = (self.cleaned_data.get("chave_serial") or "").strip()
        if not chave:
            raise ValidationError("Informe a chave/serial da licença.")

        qs = Licenca.objects.filter(chave_serial__iexact=chave)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise ValidationError("Essa chave/serial já está cadastrada (ignorando maiúsculas/minúsculas).")

        return chave

    def clean(self):
        cleaned = super().clean()
        status = cleaned.get("status")
        usuario = (cleaned.get("usuario_atual") or "").strip()

        if status == "EM_USO" and not usuario:
            self.add_error("usuario_atual", "Informe o nome da pessoa que está usando a licença.")

        # impede trocar usuário mantendo EM_USO
        if self.instance and self.instance.pk:
            old = Licenca.objects.filter(pk=self.instance.pk).values("status", "usuario_atual").first()
            if old:
                old_status = old["status"]
                old_usuario = (old["usuario_atual"] or "").strip()
                if old_status == "EM_USO" and status == "EM_USO" and old_usuario and usuario and old_usuario != usuario:
                    raise ValidationError(
                        "Esta licença já está EM USO por outra pessoa. "
                        "Para alterar, primeiro marque como LIVRE e salve; depois marque EM USO com o novo usuário."
                    )

        return cleaned


class LicencaUsoForm(forms.ModelForm):
    class Meta:
        model = LicencaUso
        fields = "__all__"
