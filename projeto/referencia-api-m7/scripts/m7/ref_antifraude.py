import random
import time

import httpx

TRANSITORIOS = {429, 502, 503, 504}


class AntifraudeClient:
    def __init__(self, client: httpx.Client, dormir=None, aleatorio=random.random, tentativas=3):
        self.http, self.aleatorio, self.tentativas = client, aleatorio, tentativas
        self.dormir = dormir or time.sleep

    def consultar(self, pedido_id):
        for n in range(self.tentativas):
            try:
                r = self.http.get("/score", params={"pedido": pedido_id})
            except (httpx.ConnectError, httpx.TimeoutException):
                r = None
            if r is not None and r.status_code not in TRANSITORIOS:
                r.raise_for_status()                                  # 4xx: erro de verdade, não repete
                return r.json()["risco"]
            if n == self.tentativas - 1:
                return None                                           # "desconhecido": segue para revisão manual
            espera = float(r.headers["Retry-After"]) if r is not None and "Retry-After" in r.headers else 0.2 * 2 ** n * self.aleatorio()
            self.dormir(espera)


def test_503_depois_ok():
    respostas = iter([httpx.Response(503), httpx.Response(200, json={"risco": 12})])
    cli = AntifraudeClient(httpx.Client(base_url="http://x", transport=httpx.MockTransport(lambda req: next(respostas))), dormir=lambda s: None)
    assert cli.consultar(1) == 12


def test_429_respeita_retry_after():
    esperas = []
    respostas = iter([httpx.Response(429, headers={"Retry-After": "2"}), httpx.Response(200, json={"risco": 5})])
    cli = AntifraudeClient(httpx.Client(base_url="http://x", transport=httpx.MockTransport(lambda r: next(respostas))), dormir=esperas.append)
    assert cli.consultar(1) == 5 and esperas == [2.0]


def test_esgota_e_devolve_desconhecido():
    cli = AntifraudeClient(httpx.Client(base_url="http://x", transport=httpx.MockTransport(lambda r: httpx.Response(503))), dormir=lambda s: None)
    assert cli.consultar(1) is None


def test_404_nao_repete():
    chamadas = []
    def h(r):
        chamadas.append(1); return httpx.Response(404)
    cli = AntifraudeClient(httpx.Client(base_url="http://x", transport=httpx.MockTransport(h)), dormir=lambda s: None)
    try:
        cli.consultar(1)
    except httpx.HTTPStatusError:
        pass
    assert len(chamadas) == 1


if __name__ == "__main__":
    for nome, fn in list(globals().items()):
        if nome.startswith("test_"):
            fn(); print("ok", nome)
