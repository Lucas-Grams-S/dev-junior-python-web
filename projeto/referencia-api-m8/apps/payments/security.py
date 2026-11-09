"""Assinatura de webhooks no estilo Stripe: `X-Signature: t=<unix>,v1=<hex>` com v1 = HMAC-SHA256(segredo, f"{t}.{corpo_bruto}")."""
import hashlib
import hmac
import time

TOLERANCIA = 300                                              # segundos: acima disso, é replay


class AssinaturaInvalida(Exception):
    pass


def assinar(segredo: str, corpo: bytes, agora: int | None = None) -> str:
    t = int(agora if agora is not None else time.time())
    v1 = hmac.new(segredo.encode(), f"{t}.".encode() + corpo, hashlib.sha256).hexdigest()
    return f"t={t},v1={v1}"


def verificar(segredo: str, corpo: bytes, cabecalho: str | None, agora: int | None = None) -> None:
    if not cabecalho:
        raise AssinaturaInvalida("cabeçalho ausente")
    try:
        partes = dict(p.split("=", 1) for p in cabecalho.split(","))
        t, recebida = int(partes["t"]), partes["v1"]
    except (KeyError, ValueError):
        raise AssinaturaInvalida("cabeçalho malformado") from None
    esperada = hmac.new(segredo.encode(), f"{t}.".encode() + corpo, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(esperada, recebida):          # tempo constante: não vaza quantos caracteres bateram
        raise AssinaturaInvalida("assinatura não confere")
    if abs((agora if agora is not None else time.time()) - t) > TOLERANCIA:
        raise AssinaturaInvalida("timestamp fora da tolerância (replay?)")
