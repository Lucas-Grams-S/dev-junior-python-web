from django.contrib import admin
from django.urls import include, path

from apps.payments.api import webhook_pagamentos

from . import views_demo
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/webhooks/payments/", webhook_pagamentos, name="webhook-payments"),
    path("demo/sync/", views_demo.espera_sync),
    path("demo/async/", views_demo.espera_async),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    path("api/<str:version>/", include("config.api_urls")),
]

handler500 = "config.errors.json_500"
