from django.conf import settings
from django.contrib import admin
from django.shortcuts import redirect
from django.urls import include, path
from django.views.generic import TemplateView
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from ledger.views import _ok


class HealthView(APIView):
    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
        return Response(_ok({"status": "ok"}))


class LoginPageView(TemplateView):
    template_name = "auth/login.html"

    def get_context_data(self, **kwargs: object) -> dict:
        ctx = super().get_context_data(**kwargs)
        ctx["google_client_id"] = settings.GOOGLE_CLIENT_ID
        if hasattr(self, "request") and self.request is not None:
            ctx["google_redirect_uri"] = self.request.build_absolute_uri("/login")
        else:
            base_url = settings.API_BASE_URL.rstrip("/")
            ctx["google_redirect_uri"] = f"{base_url}/login"
        return ctx


urlpatterns = [
    # Web pages
    path("", lambda request: redirect("/login", permanent=False)),
    path("login", LoginPageView.as_view()),
    path("register", TemplateView.as_view(template_name="auth/register.html")),
    path("dashboard", TemplateView.as_view(template_name="dashboard.html")),
    path("sync/status", TemplateView.as_view(template_name="sync/status.html")),
    path("sync/pairing", TemplateView.as_view(template_name="sync/pairing.html")),
    path("receipts", TemplateView.as_view(template_name="receipts/list.html")),
    path("receipts/<str:receipt_id>", TemplateView.as_view(template_name="receipts/detail.html")),
    path("master-data/categories", TemplateView.as_view(template_name="master_data/categories.html")),
    path("master-data/shops", TemplateView.as_view(template_name="master_data/shops.html")),
    path("master-data/cards", TemplateView.as_view(template_name="master_data/cards.html")),
    path("budgets/settings", TemplateView.as_view(template_name="budgets/settings.html")),
    path("budgets/overview", TemplateView.as_view(template_name="budgets/overview.html")),
    path("analytics/dashboard", TemplateView.as_view(template_name="analytics/dashboard.html")),
    # API
    path("admin/", admin.site.urls),
    path("api/v1/", include("accounts.urls")),
    path("api/v1/", include("ledger.urls")),
    path("api/v1/health/", HealthView.as_view()),
]
