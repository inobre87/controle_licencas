import io
from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import HttpResponse
from django.shortcuts import render

from openpyxl import Workbook

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors

from .models import Licenca, Produto, Fornecedor


def _parse_date(s: str):
    if not s:
        return None
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except ValueError:
        return None


def _filtrar_queryset(request):
    qs = Licenca.objects.select_related(
        "produto",
        "departamento",
        "compra_nf",
        "compra_nf__fornecedor",
    )

    status = request.GET.get("status") or ""
    fabricante = request.GET.get("fabricante") or ""
    fornecedor_id = request.GET.get("fornecedor") or ""
    linha = request.GET.get("linha") or ""
    data_de = _parse_date(request.GET.get("data_de") or "")
    data_ate = _parse_date(request.GET.get("data_ate") or "")

    if status:
        qs = qs.filter(status=status)
    if fabricante:
        qs = qs.filter(produto__fabricante=fabricante)
    if fornecedor_id:
        qs = qs.filter(compra_nf__fornecedor_id=fornecedor_id)
    if linha:
        qs = qs.filter(produto__linha=linha)
    if data_de:
        qs = qs.filter(compra_nf__data_compra__gte=data_de)
    if data_ate:
        qs = qs.filter(compra_nf__data_compra__lte=data_ate)

    return qs


@login_required
def dashboard(request):
    total = Licenca.objects.count()
    livres = Licenca.objects.filter(status="LIVRE").count()
    em_uso = Licenca.objects.filter(status="EM_USO").count()

    por_linha = (
        Licenca.objects.select_related("produto")
        .values("produto__linha")
        .annotate(qtd=Count("id"))
        .order_by("-qtd")[:10]
    )

    por_fabricante = (
        Licenca.objects.select_related("produto")
        .values("produto__fabricante")
        .annotate(qtd=Count("id"))
        .order_by("-qtd")
    )

    por_departamento = (
        Licenca.objects.select_related("departamento")
        .values("departamento__nome")
        .annotate(qtd=Count("id"))
        .order_by("-qtd")
    )

    context = {
        "total": total,
        "livres": livres,
        "em_uso": em_uso,
        "por_linha_labels": [x["produto__linha"] for x in por_linha],
        "por_linha_data": [x["qtd"] for x in por_linha],
        "por_fabricante_labels": [x["produto__fabricante"] for x in por_fabricante],
        "por_fabricante_data": [x["qtd"] for x in por_fabricante],
        "por_departamento_labels": [
            x["departamento__nome"] or "Sem departamento" for x in por_departamento
        ],
        "por_departamento_data": [x["qtd"] for x in por_departamento],
    }
    return render(request, "dashboard.html", context)


@login_required
def relatorios(request):
    qs = _filtrar_queryset(request)

    fornecedores = Fornecedor.objects.order_by("nome")
    linhas = (
        Produto.objects.values_list("linha", flat=True).distinct().order_by("linha")
    )

    context = {
        # FIX: atualizado_em não existe -> usar -id (mais recente primeiro)
        "licencas": qs.order_by("-id")[:500],
        "status": request.GET.get("status", ""),
        "fabricante": request.GET.get("fabricante", ""),
        "fornecedor": request.GET.get("fornecedor", ""),
        "linha": request.GET.get("linha", ""),
        "data_de": request.GET.get("data_de", ""),
        "data_ate": request.GET.get("data_ate", ""),
        "fornecedores": fornecedores,
        "linhas": linhas,
    }
    return render(request, "relatorios.html", context)


@login_required
def exportar_excel(request):
    qs = _filtrar_queryset(request).order_by(
        "departamento__nome",
        "usuario_atual",
        "produto__fabricante",
        "produto__linha",
        "produto__versao_edicao",
    )

    wb = Workbook()
    ws = wb.active
    ws.title = "Licencas"

    ws.append([
        "Departamento",
        "Colaborador",
        "Fabricante",
        "Linha",
        "Versão",
        "Chave",
        "Status",
        "Fornecedor",
        "Data compra",
        "NF",
    ])

    for lic in qs:
        ws.append([
            getattr(lic.departamento, "nome", "") or "Sem departamento",
            lic.usuario_atual or "-",
            lic.produto.get_fabricante_display(),
            lic.produto.linha,
            lic.produto.versao_edicao,
            lic.chave_serial,
            "Em uso" if lic.status == "EM_USO" else "Livre",
            lic.compra_nf.fornecedor.nome,
            lic.compra_nf.data_compra.strftime("%d/%m/%Y") if lic.compra_nf.data_compra else "",
            lic.compra_nf.numero_nf or "",
        ])

    out = io.BytesIO()
    wb.save(out)
    out.seek(0)

    resp = HttpResponse(
        out.read(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    resp["Content-Disposition"] = 'attachment; filename="relatorio_licencas.xlsx"'
    return resp


@login_required
def exportar_pdf(request):
    qs = _filtrar_queryset(request).order_by(
        "departamento__nome",
        "usuario_atual",
        "produto__linha",
        "produto__versao_edicao",
    )

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    c.setTitle("Relatório de Licenças")
    c.setFont("Helvetica-Bold", 14)
    c.drawString(20 * mm, height - 20 * mm, "Relatório de Licenças")
    c.setFont("Helvetica", 9)
    c.drawString(
        20 * mm,
        height - 26 * mm,
        f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
    )

    # FIX: cabeçalho e linhas com o MESMO número de colunas
    data = [[
        "Departamento",
        "Colaborador",
        "Produto",
        "Chave/Serial",
        "Status",
        "Fornecedor",
        "Compra",
        "NF",
    ]]

    for lic in qs[:800]:
        data.append([
            getattr(lic.departamento, "nome", "") or "Sem departamento",
            lic.usuario_atual or "-",
            str(lic.produto),
            lic.chave_serial,
            "Em uso" if lic.status == "EM_USO" else "Livre",
            lic.compra_nf.fornecedor.nome,
            lic.compra_nf.data_compra.strftime("%d/%m/%Y") if lic.compra_nf.data_compra else "",
            lic.compra_nf.numero_nf or "",
        ])

    table = Table(
        data,
        colWidths=[28*mm, 28*mm, 45*mm, 35*mm, 16*mm, 32*mm, 18*mm, 12*mm],
    )
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))

    tw, th = table.wrapOn(c, width - 40 * mm, height - 60 * mm)
    x = 20 * mm
    y = height - 35 * mm - th
    if y < 20 * mm:
        y = 20 * mm
    table.drawOn(c, x, y)

    c.showPage()
    c.save()

    pdf = buffer.getvalue()
    buffer.close()

    resp = HttpResponse(pdf, content_type="application/pdf")
    resp["Content-Disposition"] = 'attachment; filename="relatorio_licencas.pdf"'
    return resp
