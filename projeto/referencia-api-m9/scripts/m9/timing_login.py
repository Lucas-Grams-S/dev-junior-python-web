"""O tempo do login revela se o usuário existe? Mede a mediana de usuário EXISTENTE com senha errada x usuário INEXISTENTE."""
import os, statistics, sys, time
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
sys.path.insert(0, os.environ["LAB"])
import django
django.setup()
import logging
logging.getLogger().handlers.clear()
from django.core.cache import cache
from django.test import Client

def tempo(usuario, n=15):
    amostras = []
    for i in range(n):
        cache.clear()                     # sem isso o limite de tentativas (429) distorce a medição
        t = time.perf_counter()
        r = Client().post("/api/v1/auth/token/", {"username": usuario, "password": "errada-errada-123"}, content_type="application/json")
        amostras.append(time.perf_counter() - t)
        assert r.status_code == 401
    return statistics.median(amostras) * 1000

Client().post("/api/v1/auth/token/", {"username": "cliente", "password": "x"}, content_type="application/json")   # aquecimento
a, b = tempo("cliente"), tempo("usuario_que_nao_existe")
print(f"usuário existente, senha errada : mediana {a:7.1f} ms")
print(f"usuário inexistente             : mediana {b:7.1f} ms")
print(f"diferença                       : {abs(a - b):7.1f} ms ({abs(a - b) / max(a, b) * 100:.0f}% do maior)")
