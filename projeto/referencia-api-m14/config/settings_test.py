"""Configuração SÓ para a suíte de testes. Tudo o mais é igual à de produção (herda de `config.settings`)."""

from django.contrib.auth.hashers import PBKDF2PasswordHasher

from .settings import *


class HasherRapidoParaTestes(PBKDF2PasswordHasher):
    """Mesmo formato do PBKDF2, mas com 1 iteração: criar um usuário custa microssegundos, não ~50 ms de Argon2."""

    iterations = 1


PASSWORD_HASHERS = ["config.settings_test.HasherRapidoParaTestes"]
