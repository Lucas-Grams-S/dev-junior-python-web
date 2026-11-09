"""Compara, consulta a consulta, as respostas do catálogo em Django/DRF e em FastAPI (mesmo seed).

Uso (os dois servidores no ar):
    uv run python scripts/comparar.py http://localhost:8816 http://localhost:8815
"""

import re
import sys

import httpx

CONSULTAS = [
    "",
    "?page_size=7&page=3",
    "?page_size=1000",
    "?category=audio",
    "?price_min=500&price_max=900",
    "?in_stock=true&ordering=-price",
    "?search=mouse",
    "?search=MOUSE&ordering=price",
    "?category=casa&in_stock=false",
    "?ordering=-created_at&page_size=5",
    "?page=99",  # fora do intervalo
    "?page=0",
    "?ordering=password",
    "1/",
    "17/",  # inativo
    "999999/",
]
IGNORA = {"created_at", "image_url"}  # image_url só existe no Django (módulo 13); created_at difere por instante de criação


def limpa(x):
    if isinstance(x, dict):
        return {k: limpa(v) for k, v in x.items() if k not in IGNORA}
    if isinstance(x, list):
        return [limpa(v) for v in x]
    if isinstance(x, str) and x.startswith("http"):  # next/previous: host e ORDEM dos parâmetros podem variar
        return re.sub(r"^https?://[^/]+", "", x) and sorted(x.split("?", 1)[1].split("&"))
    return x


def main(dj: str, fa: str) -> int:
    diferentes = 0
    with httpx.Client() as c:
        for q in CONSULTAS:
            a = c.get(f"{dj}/api/v1/products/{q}")
            b = c.get(f"{fa}/api/v1/products/{q}")
            ja, jb = (limpa(a.json()) if a.status_code == 200 else None), (limpa(b.json()) if b.status_code == 200 else None)
            igual = a.status_code == b.status_code and ja == jb
            diferentes += not igual
            print(f"{'IGUAL    ' if igual else 'DIFERENTE'} DRF={a.status_code} FastAPI={b.status_code}  /products/{q}")
            if a.status_code != 200 or b.status_code != 200:
                if not igual:
                    print(f"          DRF    : {a.text[:110]}\n          FastAPI: {b.text[:110]}")
    return diferentes


if __name__ == "__main__":
    sys.exit(1 if main(sys.argv[1], sys.argv[2]) else 0)
