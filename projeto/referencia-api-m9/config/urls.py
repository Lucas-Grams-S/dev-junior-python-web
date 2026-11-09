from django.conf import settings
from django.contrib import admin
from django.urls import include, path

from apps.payments.api import webhook_pagamentos

from . import views_demo
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),
    path("api/v1/webhooks/payments/", webhook_pagamentos, name="webhook-payments"),
]
if settings.ENABLE_DEMO_ROUTES:                      # rotas de experimento: só em desenvolvimento
    urlpatterns += [path("demo/sync/", views_demo.espera_sync), path("demo/async/", views_demo.espera_async)]
if settings.EXPOSE_DOCS:                              # documentação da API: ligada por decisão (EXPOSE_DOCS=1) ou em DEBUG
    urlpatterns += [
        path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
        path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
        path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    ]
urlpatterns.append(path("api/<str:version>/", include("config.api_urls")))

handler500 = "config.errors.json_500"
