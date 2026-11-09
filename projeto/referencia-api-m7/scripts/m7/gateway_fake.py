"""O 'gateway de pagamento' de mentira: assina e envia webhooks, e REPETE quando o destino não responde 2xx (como os reais)."""
import json
import time
import uuid

import httpx

from apps.payments.security import assinar


def evento(tipo, payment_ref, amount, event_id=None):
    return {"id": event_id or "evt_" + uuid.uuid4().hex[:12], "type": tipo, "created": int(time.time()),
            "data": {"payment_ref": payment_ref, "amount": str(amount), "currency": "BRL"}}


def enviar(url, segredo, ev, *, corpo=None, cabecalho=None, timestamp=None, tentativas=1, espera=0.2, dormir=time.sleep):
    """Envia o evento. `corpo`/`cabecalho` permitem forjar ataques. Repete (como o gateway) enquanto não vier 2xx."""
    bruto = corpo if corpo is not None else json.dumps(ev, separators=(",", ":")).encode()
    assinatura = cabecalho if cabecalho is not None else assinar(segredo, bruto, agora=timestamp)
    for n in range(tentativas):
        r = httpx.post(url, content=bruto, headers={"Content-Type": "application/json", "X-Signature": assinatura}, timeout=5)
        if 200 <= r.status_code < 300:
            return r, n + 1
        if n + 1 < tentativas:
            dormir(espera * 2 ** n)                                   # backoff do gateway
    return r, tentativas
