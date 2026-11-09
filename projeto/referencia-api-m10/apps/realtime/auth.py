"""Autenticação do WebSocket: o navegador NÃO consegue enviar o cabeçalho Authorization em `new WebSocket(...)`,
então o access token JWT vai na query string (curto e de uso único para a conexão). Nunca registre a URL completa em logs."""

import contextlib
from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken


@database_sync_to_async
def _usuario(user_id):
    return get_user_model().objects.filter(pk=user_id, is_active=True).first()


class JWTQueryMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        token = parse_qs(scope.get("query_string", b"").decode()).get("token", [None])[0]
        scope["user"] = None
        if token:
            with contextlib.suppress(TokenError):  # token inválido/expirado: segue anônimo
                scope["user"] = await _usuario(AccessToken(token)["user_id"])
        return await self.app(scope, receive, send)
