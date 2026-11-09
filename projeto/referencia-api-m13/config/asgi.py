import os

from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django_asgi_app = get_asgi_application()

from apps.realtime.auth import JWTQueryMiddleware  # noqa: E402  (depois do setup do Django)
from apps.realtime.routing import websocket_urlpatterns  # noqa: E402

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": JWTQueryMiddleware(URLRouter(websocket_urlpatterns)),  # type: ignore[arg-type]  # incompatibilidade de tipos django-stubs × Channels,
    }
)
