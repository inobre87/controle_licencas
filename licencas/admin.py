from django.contrib import admin
from .models import Fornecedor, CompraNF, Produto, Licenca, LicencaUso, Departamento, LicencaLivre
from .forms import LicencaForm


@admin.register(Departamento)
class DepartamentoAdmin(admin.ModelAdmin):
    list_display = ["nome", "ativo"]
    search_fields = ["nome"]
    list_filter = ["ativo"]


@admin.register(Fornecedor)
class FornecedorAdmin(admin.ModelAdmin):
    search_fields = ["nome", "cnpj", "email"]
    list_display = ["nome", "cnpj", "email", "telefone"]
    ordering = ["nome"]


@admin.register(CompraNF)
class CompraNFAdmin(admin.ModelAdmin):
    search_fields = ["fornecedor__nome", "numero_nf", "vendedor"]
    list_filter = ["fornecedor", "data_compra"]
    list_display = ["fornecedor", "data_compra", "numero_nf", "vendedor", "valor_total", "arquivo_pdf"]
    date_hierarchy = "data_compra"
    autocomplete_fields = ["fornecedor"]


@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    search_fields = ["linha", "versao_edicao"]
    list_filter = ["fabricante", "ativo", "linha"]
    list_display = ["fabricante", "linha", "versao_edicao", "ativo"]
    list_editable = ["ativo"]


class LicencaUsoInline(admin.TabularInline):
    model = LicencaUso
    extra = 0
    readonly_fields = ["data_inicio", "data_fim"]
    can_delete = False


@admin.register(Licenca)
class LicencaAdmin(admin.ModelAdmin):
    form = LicencaForm

    search_fields = [
        "chave_serial",
        "produto__linha",
        "produto__versao_edicao",
        "compra_nf__fornecedor__nome",
        "usuario_atual",
    ]
    list_filter = ["status", "departamento", "produto__fabricante"]
    list_display = [
        "produto",
        "departamento",
        "status",
        "usuario_atual",
        "fornecedor",
        "data_compra",
        "numero_nf",
        "chave_serial",
    ]
    autocomplete_fields = ["produto", "compra_nf"]
    inlines = [LicencaUsoInline]

    def fornecedor(self, obj):
        return obj.compra_nf.fornecedor
    fornecedor.admin_order_field = "compra_nf__fornecedor__nome"

    def data_compra(self, obj):
        return obj.compra_nf.data_compra
    data_compra.admin_order_field = "compra_nf__data_compra"

    def numero_nf(self, obj):
        return obj.compra_nf.numero_nf
    numero_nf.admin_order_field = "compra_nf__numero_nf"


# ✅ MENU SEPARADO: "Licenças Livres"
@admin.register(LicencaLivre)
class LicencaLivreAdmin(LicencaAdmin):
    # herda tudo do LicencaAdmin (inclui form e inline)
    # só muda o queryset pra mostrar apenas LIVRE
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(status="LIVRE")
