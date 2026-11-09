"""Monitoramento de erros com Sentry (aula 14.02). Só liga se SENTRY_DSN existir; nunca envia dados pessoais por padrão."""

import os
import re

SENSIVEIS = re.compile(r"(passw|senha|secret|token|authorization|cookie|api[-_]?key|csrf|session)", re.I)


def _limpar(obj):
    if isinstance(obj, dict):
        return {k: "[Filtered]" if SENSIVEIS.search(str(k)) else _limpar(v) for k, v in obj.items()}
    if isinstance(obj, list | tuple):
        return [_limpar(v) for v in obj]
    return obj


def scrub(event, hint):
    """`before_send`: última barreira antes de o evento sair. Remove cabeçalhos, cookies, corpo e query string da requisição."""
    req = event.get("request")
    if req:
        req["headers"] = _limpar(req.get("headers") or {})
        req.pop("cookies", None)
        req.pop("data", None)  # corpo (senhas, cartões…): fora
        if req.get("query_string"):
            req["query_string"] = "[Filtered]"
    if "extra" in event:
        event["extra"] = _limpar(event["extra"])
    return event


def init_sentry(transport=None) -> bool:
    """Retorna True se o Sentry foi ligado. `transport` existe para os TESTES (captura os eventos sem rede)."""
    dsn = os.environ.get("SENTRY_DSN", "")
    if not dsn:
        return False
    import sentry_sdk

    sentry_sdk.init(
        dsn=dsn,
        environment=os.environ.get("SENTRY_ENVIRONMENT", "production"),
        release=os.environ.get("RELEASE") or None,  # tag da imagem / commit: ligar o erro ao deploy que o causou
        # sentry-sdk 2.x: `send_default_pii` está DEPRECIADA (gera DeprecationWarning); o controle fino é `data_collection`.
        data_collection={
            "user_info": False,
            "http_bodies": [],
            "stack_frame_variables": False,
        },  # sem usuário/IP, sem corpos, sem valores de variáveis
        traces_sample_rate=float(os.environ.get("SENTRY_TRACES_SAMPLE_RATE", "0")),  # desempenho por amostragem; 0 = desligado
        before_send=scrub,
        transport=transport,
    )
    return True
