"""Eventos de segurança: quem tentou, quando e de onde (nunca a senha)."""

import logging

from django.contrib.auth.signals import user_login_failed
from django.dispatch import receiver

seguranca = logging.getLogger("security")


def limpo(valor, limite=64):
    """Evita *log injection*: sem quebras de linha nem caracteres de controle, e com tamanho limitado."""
    return "".join(ch if ch.isprintable() else "?" for ch in str(valor))[:limite]


def ip_do_cliente(request):
    if request is None:
        return "-"
    return limpo(request.META.get("REMOTE_ADDR", "-"), 45)


@receiver(user_login_failed)
def registrar_login_falho(sender, credentials, request=None, **kwargs):
    seguranca.warning("login_failed username=%s ip=%s", limpo(credentials.get("username", "-")), ip_do_cliente(request))
