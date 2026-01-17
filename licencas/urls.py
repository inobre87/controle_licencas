from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path("login/", auth_views.LoginView.as_view(template_name="auth/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),

    path("", views.dashboard, name="dashboard"),
    path("relatorios/", views.relatorios, name="relatorios"),
    path("relatorios/excel/", views.exportar_excel, name="exportar_excel"),
    path("relatorios/pdf/", views.exportar_pdf, name="exportar_pdf"),
]
