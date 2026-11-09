"""Verificação das defesas do MiniShop: CSRF (sessão), cookies, JWT e CORS. Tudo contra o laboratório local, em modo produção."""
import base64
import json
import os
import re
import sys

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
sys.path.insert(0, os.environ["LAB"])
django.setup()
import logging  # noqa: E402

logging.getLogger().handlers.clear()
from django.contrib.auth import get_user_model  # noqa: E402
from django.core.cache import cache  # noqa: E402
from django.test import Client  # noqa: E402

User = get_user_model()
SENHA = "dev-somente-local-123"
User.objects.filter(username="adm_tmp").delete()
User.objects.create_superuser("adm_tmp", "a@exemplo.com", SENHA)

print("== 1) CSRF numa rota que usa COOKIE de sessão (login do admin), com a verificação ligada")
c = Client(enforce_csrf_checks=True)
r = c.post("/admin/login/", {"username": "adm_tmp", "password": SENHA, "next": "/admin/"}, secure=True)
print(f"   POST sem token CSRF                    → {r.status_code}  (403 = recusado pelo Django)")
g = c.get("/admin/login/", secure=True)
token = c.cookies["csrftoken"].value
r = c.post("/admin/login/", {"username": "adm_tmp", "password": SENHA, "next": "/admin/", "csrfmiddlewaretoken": token}, secure=True, HTTP_REFERER="https://testserver/admin/login/")
print(f"   POST com token CSRF + Referer válido   → {r.status_code}  (302 = login aceito)")
r2 = Client(enforce_csrf_checks=True)
r2.get("/admin/login/", secure=True)
t2 = r2.cookies["csrftoken"].value
r = r2.post("/admin/login/", {"username": "adm_tmp", "password": SENHA, "csrfmiddlewaretoken": t2}, secure=True, HTTP_REFERER="https://site-malicioso.example/pagina")
print(f"   token válido, mas Referer de OUTRO site → {r.status_code}  (403: em HTTPS o Django confere o Referer/Origin)")

print("\n== 2) Atributos dos cookies emitidos no login (DEBUG=0)")
for nome in ("csrftoken", "sessionid"):
    m = c.cookies.get(nome)
    if m:
        print(f"   {nome:<10} Secure={bool(m['secure'])!s:<5} HttpOnly={bool(m['httponly'])!s:<5} SameSite={m['samesite'] or '(não definido)'}")

print("\n== 3) A API usa JWT no cabeçalho Authorization (o navegador NÃO o anexa sozinho)")
cache.clear()
tok = Client().post("/api/v1/auth/token/", {"username": "cliente", "password": SENHA}, content_type="application/json").json()
h, p, s = tok["access"].split(".")
dec = lambda x: json.loads(base64.urlsafe_b64decode(x + "=" * (-len(x) % 4)))
print("   cabeçalho:", dec(h))
pl = dec(p)
print("   payload  :", {k: pl[k] for k in pl if k != "jti"}, "(qualquer um LÊ; o que ninguém faz é ASSINAR)")
print(f"   validade do access: {pl['exp'] - pl['iat']} s")
ok = Client(HTTP_AUTHORIZATION="Bearer " + tok["access"]).get("/api/v1/auth/me/").status_code
adulterado = h + "." + base64.urlsafe_b64encode(json.dumps({**pl, "user_id": "1"}).encode()).rstrip(b"=").decode() + "." + s
bad = Client(HTTP_AUTHORIZATION="Bearer " + adulterado).get("/api/v1/auth/me/").status_code
sem_assin = base64.urlsafe_b64encode(json.dumps({"alg": "none", "typ": "JWT"}).encode()).rstrip(b"=").decode() + "." + p + "."
nenhum = Client(HTTP_AUTHORIZATION="Bearer " + sem_assin).get("/api/v1/auth/me/").status_code
print(f"   token válido → {ok} · payload alterado (assinatura antiga) → {bad} · algoritmo 'none' sem assinatura → {nenhum}")

print("\n== 4) Logout: sessão x JWT")
cache.clear()
cli = Client(HTTP_AUTHORIZATION="Bearer " + tok["access"])
lg = cli.post("/api/v1/auth/logout/", {"refresh": tok["refresh"]}, content_type="application/json")
rf = Client().post("/api/v1/auth/token/refresh/", {"refresh": tok["refresh"]}, content_type="application/json")
print(f"   logout (refresh vai para a lista negra) → {lg.status_code}; usar o refresh de novo → {rf.status_code}")
print(f"   o ACCESS antigo continua valendo até expirar → {cli.get('/api/v1/auth/me/').status_code}  (é por isso que ele dura só {pl['exp'] - pl['iat']} s)")
cs = Client()
cs.login(username="adm_tmp", password=SENHA)
a = cs.get("/admin/", secure=True).status_code
cs.logout()
print(f"   sessão: antes do logout → {a}; depois (a sessão some NO SERVIDOR) → {cs.get('/admin/', secure=True).status_code}")

print("\n== 5) CORS: quem pode LER respostas da API de outra origem")
for origem in ("http://127.0.0.1:8200", "https://site-malicioso.example"):
    r = Client().options("/api/v1/orders/", HTTP_ORIGIN=origem, HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST", HTTP_ACCESS_CONTROL_REQUEST_HEADERS="authorization,content-type")
    print(f"   preflight de {origem:<32} → {r.status_code}  Allow-Origin={r.headers.get('Access-Control-Allow-Origin')!r}  Allow-Credentials={r.headers.get('Access-Control-Allow-Credentials')!r}")

User.objects.filter(username="adm_tmp").delete()
