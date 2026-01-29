from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db.models.functions import Lower


class Fornecedor(models.Model):
    nome = models.CharField(max_length=180, unique=True)
    cnpj = models.CharField(max_length=18, blank=True)
    email = models.EmailField(blank=True)
    telefone = models.CharField(max_length=30, blank=True)

    class Meta:
        ordering = ["nome"]
        verbose_name = "Cadastro • Fornecedor"
        verbose_name_plural = "Cadastros • Fornecedores"

    def __str__(self):
        return self.nome


class CompraNF(models.Model):
    fornecedor = models.ForeignKey(Fornecedor, on_delete=models.PROTECT, related_name="compras")
    data_compra = models.DateField()
    vendedor = models.CharField(max_length=120, blank=True)
    numero_nf = models.CharField(max_length=60, blank=True)
    valor_total = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    arquivo_pdf = models.FileField(upload_to="notas_fiscais/%Y/%m/")  # obrigatório
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-data_compra", "-id"]
        verbose_name = "Cadastro • Compra (NF)"
        verbose_name_plural = "Cadastros • Compras (NFs)"

    def __str__(self):
        base = f"{self.fornecedor} - {self.data_compra:%d/%m/%Y}"
        return f"{base} (NF {self.numero_nf})" if self.numero_nf else base


class Produto(models.Model):
    FABRICANTE_CHOICES = [
        ("MICROSOFT", "Microsoft"),
        ("COREL", "Corel"),
        ("ADOBE", "Adobe"),
        ("OUTRO", "Outro"),
    ]

    fabricante = models.CharField(max_length=20, choices=FABRICANTE_CHOICES, default="MICROSOFT")
    linha = models.CharField(max_length=80, help_text="Ex: Windows, Windows Server, Office, CorelDRAW")
    versao_edicao = models.CharField(max_length=120, help_text="Ex: 11 Pro, Server 2022 Standard, Office 2021, etc.")
    ativo = models.BooleanField(default=True)

    class Meta:
        unique_together = ("fabricante", "linha", "versao_edicao")
        ordering = ["fabricante", "linha", "versao_edicao"]
        verbose_name = "Cadastro • Produto"
        verbose_name_plural = "Cadastros • Produtos"

    def __str__(self):
        fab = dict(self.FABRICANTE_CHOICES).get(self.fabricante, self.fabricante)
        return f"{fab} • {self.linha} • {self.versao_edicao}"


class Departamento(models.Model):
    nome = models.CharField(max_length=120, unique=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ["nome"]
        verbose_name = "Gestão • Departamento"
        verbose_name_plural = "Gestão • Departamentos"

    def __str__(self):
        return self.nome


class Licenca(models.Model):
    STATUS_LICENCA = [
        ("LIVRE", "Livre"),
        ("EM_USO", "Em uso"),
    ]

    produto = models.ForeignKey(Produto, on_delete=models.PROTECT, related_name="licencas")
    departamento = models.ForeignKey(
        Departamento,
        on_delete=models.PROTECT,
        related_name="licencas",
        null=True,
        blank=True,
    )
    chave_serial = models.CharField(max_length=255, unique=True)
    compra_nf = models.ForeignKey(CompraNF, on_delete=models.PROTECT, related_name="licencas")

    status = models.CharField(max_length=10, choices=STATUS_LICENCA, default="LIVRE")
    usuario_atual = models.CharField(
        max_length=120,
        blank=True,
        help_text="Obrigatório apenas quando o status for 'Em uso'."
    )
    observacoes = models.TextField(blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                Lower("chave_serial"),
                name="uniq_licenca_chave_serial_ci",
            )
        ]
        verbose_name = "Gestão • Licença"
        verbose_name_plural = "Gestão • Licenças"

    def clean(self):
        if self.status == "EM_USO" and not (self.usuario_atual or "").strip():
            raise ValidationError({"usuario_atual": "Informe o nome da pessoa que está usando a licença."})

        # impede trocar usuário com status EM_USO sem liberar antes
        if self.pk:
            old = Licenca.objects.filter(pk=self.pk).values("status", "usuario_atual").first()
            if old:
                old_status = old["status"]
                old_usuario = (old["usuario_atual"] or "").strip()
                new_usuario = (self.usuario_atual or "").strip()
                if old_status == "EM_USO" and self.status == "EM_USO" and old_usuario and new_usuario and old_usuario != new_usuario:
                    raise ValidationError({
                        "usuario_atual": (
                            "Esta licença já está EM USO por outra pessoa. "
                            "Para alterar, primeiro marque como LIVRE e salve; depois marque EM USO com o novo usuário."
                        )
                    })

        # unicidade case-insensitive também antes do banco
        if self.chave_serial:
            qs = Licenca.objects.filter(chave_serial__iexact=self.chave_serial.strip())
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError({"chave_serial": "Já existe uma licença cadastrada com esta mesma chave (ignorando maiúsculas/minúsculas)."})

    def save(self, *args, **kwargs):
        old_status = None
        if self.pk:
            old_status = Licenca.objects.filter(pk=self.pk).values_list("status", flat=True).first()

        if self.status == "LIVRE":
            self.usuario_atual = ""

        super().save(*args, **kwargs)

        # histórico por mudança de status
        if old_status != self.status:
            if self.status == "EM_USO":
                LicencaUso.objects.create(licenca=self, pessoa=self.usuario_atual, data_inicio=timezone.now())
            elif self.status == "LIVRE":
                uso_aberto = LicencaUso.objects.filter(
                    licenca=self,
                    data_fim__isnull=True
                ).order_by("-data_inicio").first()
                if uso_aberto:
                    uso_aberto.data_fim = timezone.now()
                    uso_aberto.save(update_fields=["data_fim"])

    def __str__(self):
        return f"{self.produto} • {self.chave_serial}"


class LicencaUso(models.Model):
    licenca = models.ForeignKey(Licenca, on_delete=models.CASCADE, related_name="historico_uso")
    pessoa = models.CharField(max_length=120)
    data_inicio = models.DateTimeField()
    data_fim = models.DateTimeField(null=True, blank=True)
    observacao = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-data_inicio"]
        verbose_name = "Histórico • Uso de Licença"
        verbose_name_plural = "Histórico • Usos de Licença"

    def __str__(self):
        fim = self.data_fim.strftime("%d/%m/%Y %H:%M") if self.data_fim else "em aberto"
        return f"{self.pessoa} ({self.data_inicio:%d/%m/%Y %H:%M} → {fim})"


# ✅ PROXY MODEL: não cria tabela, só cria um "menu" separado no admin
class LicencaLivre(Licenca):
    class Meta:
        proxy = True
        verbose_name = "Gestão • Licença Livre"
        verbose_name_plural = "Gestão • Licenças Livres"
