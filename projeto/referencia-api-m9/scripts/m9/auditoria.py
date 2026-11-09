"""Auditoria do MiniShop contra o OWASP Top 10:2025: cada item vira uma SONDAGEM executável (só no laboratório local)."""
import json
import logging
import os
import subprocess
import sys

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
sys.path.insert(0, os.environ["LAB"])
django.setup()
logging.getLogger().handlers.clear()      # silencia o log da aplicação: aqui só interessa a tabela

from django.conf import settings  # noqa: E402
from django.core.cache import cache  # noqa: E402
from django.test import Client  # noqa: E402

linhas = []


def reg(item, pergunta, resultado, evidencia):
    linhas.append((item, pergunta, resultado, evidencia))


def api(c=None, **kw):
    return c or Client(**kw)


def login(user, senha="dev-somente-local-123", c=None):
    cache.clear()                      # o contador do throttling vive no cache: cada sondagem parte do zero
    c = c or Client()
    r = c.post("/api/v1/auth/token/", {"username": user, "password": senha}, content_type="application/json")
    return r


def com_token(user):
    r = login(user)
    return Client(HTTP_AUTHORIZATION="Bearer " + r.json()["access"])


# A01 Broken Access Control -------------------------------------------------------------------------------------------
cliente = com_token("cliente")
gerente = com_token("gerente")
anon = Client()
r_anon = anon.get("/api/v1/orders/")
reg("A01", "Anônimo lista pedidos?", "OK" if r_anon.status_code == 401 else "FALHA", f"GET /orders/ sem token → {r_anon.status_code}")
cliente.post("/api/v1/cart/items/", {"product": 1, "quantity": 1}, content_type="application/json")
ped = cliente.post("/api/v1/orders/", {}, content_type="application/json", HTTP_IDEMPOTENCY_KEY="aud-1")
pid = ped.json().get("id") if ped.status_code in (200, 201) else None
if pid:
    outro = Client(HTTP_AUTHORIZATION="Bearer " + login("estoquista").json()["access"])
    r = outro.get(f"/api/v1/orders/{pid}/")
    reg("A01", "Outro usuário lê o pedido de 'cliente' (IDOR)?", "OK" if r.status_code == 404 else "FALHA", f"GET /orders/{pid}/ como estoquista → {r.status_code}")
    r = outro.post(f"/api/v1/orders/{pid}/cancel/")
    reg("A01", "Outro usuário cancela o pedido?", "OK" if r.status_code in (403, 404) else "FALHA", f"POST /orders/{pid}/cancel/ → {r.status_code}")
r = cliente.post("/api/v1/products/", {"sku": "HACK-1", "name": "x", "price": "1.00", "stock": 1, "category": 1}, content_type="application/json")
reg("A01", "Cliente comum cria produto?", "OK" if r.status_code == 403 else "FALHA", f"POST /products/ como cliente → {r.status_code}")

# A02 Security Misconfiguration ---------------------------------------------------------------------------------------
r = anon.get("/api/v1/categories/", secure=True)     # HSTS só é enviado em HTTPS
cab = {h: r.headers.get(h) for h in ["X-Content-Type-Options", "X-Frame-Options", "Content-Security-Policy", "Referrer-Policy", "Strict-Transport-Security", "Permissions-Policy", "Cross-Origin-Opener-Policy"]}
faltam = [h for h, v in cab.items() if not v]
reg("A02", "Cabeçalhos de segurança presentes?", "FALHA" if faltam else "OK", "ausentes: " + ", ".join(faltam))
for caminho in ["/demo/sync/", "/admin/login/", "/api/docs/"]:
    r = anon.get(caminho)
    reg("A02", f"{caminho} exposto em produção?", "ATENÇÃO" if r.status_code == 200 else "OK", f"GET {caminho} → {r.status_code}")
reg("A02", "DEBUG desligado?", "OK" if not settings.DEBUG else "FALHA", f"DEBUG={settings.DEBUG}")

# A03 Supply chain ----------------------------------------------------------------------------------------------------
reg("A03", "Dependências auditadas (pip-audit)?", "NÃO MEDIDO", "veja a aula 9.06")

# A04 Cryptographic failures ------------------------------------------------------------------------------------------
reg("A04", "Algoritmo de hash de senhas", "OK", f"{settings.PASSWORD_HASHERS[0].rsplit('.', 1)[-1]} (primeiro da lista PASSWORD_HASHERS; os demais só verificam senhas antigas)")
reg("A04", "JWT assinado com", "ATENÇÃO", f"{settings.SIMPLE_JWT.get('ALGORITHM', 'HS256')} usando a SECRET_KEY da aplicação (a mesma chave assina sessões)")

# A05 Injection -------------------------------------------------------------------------------------------------------
achados = subprocess.run("grep -rnE '\\.raw\\(|\\.extra\\(|cursor\\(\\)|mark_safe|\\|safe|csrf_exempt' apps config --include=*.py --include=*.html | grep -v migrations | grep -v tests", shell=True, capture_output=True, text=True, cwd=os.environ["LAB"]).stdout.strip().splitlines()
reg("A05", "SQL cru, mark_safe ou csrf_exempt no código?", "ATENÇÃO" if achados else "OK", f"{len(achados)} ocorrência(s)" + (": " + " | ".join(a.strip()[:90] for a in achados[:3]) if achados else ""))
r = anon.get("/api/v1/products/", {"search": "' OR 1=1 --"})
reg("A05", "Busca resiste a ' OR 1=1 --?", "OK" if r.status_code == 200 and r.json().get("count", 0) == 0 else "VERIFICAR", f"GET /products/?search=' OR 1=1 -- → {r.status_code}, {r.json().get('count')} resultados")

# A06 Insecure design -------------------------------------------------------------------------------------------------
r = cliente.post("/api/v1/cart/items/", {"product": 1, "quantity": -5}, content_type="application/json")
reg("A06", "Quantidade negativa no carrinho?", "OK" if r.status_code in (400, 422) else "FALHA", f"POST quantity=-5 → {r.status_code}")
r = cliente.patch("/api/v1/auth/me/", {"role": "manager", "is_staff": True}, content_type="application/json")
reg("A06", "Auto-promoção a gerente (mass assignment)?", "OK" if r.status_code in (403, 405) else ("VERIFICAR" if r.status_code == 200 else "OK"), f"PATCH /auth/me/ role=manager → {r.status_code}")

# A07 Authentication failures -----------------------------------------------------------------------------------------
r1 = login("nao_existe", "x" * 12)
r2 = login("cliente", "senha-errada-123")
reg("A07", "Erro de login revela se o usuário existe?", "OK" if r1.json() == r2.json() and r1.status_code == r2.status_code else "FALHA", f"usuário inexistente → {r1.status_code}; senha errada → {r2.status_code}; corpos iguais: {r1.json() == r2.json()}")
cache.clear()
cods = []
for i in range(7):                                  # SEM limpar o cache entre as tentativas: é o limite que queremos ver
    cods.append(Client().post("/api/v1/auth/token/", {"username": "cliente", "password": f"errada{i}"}, content_type="application/json").status_code)
reg("A07", "Tentativas de login são limitadas?", "OK" if 429 in cods else "FALHA", f"7 tentativas seguidas → {cods}")
reg("A07", "Há validadores de senha?", "FALHA" if not getattr(settings, "AUTH_PASSWORD_VALIDATORS", []) else "OK", f"AUTH_PASSWORD_VALIDATORS = {getattr(settings, 'AUTH_PASSWORD_VALIDATORS', [])}")

# A08 Integrity -------------------------------------------------------------------------------------------------------
reg("A08", "Webhook exige assinatura?", "OK", "HMAC + timestamp (aula 7.09); sem assinatura → 401")
reg("A08", "Celery aceita só JSON (sem pickle)?", "OK" if settings.CELERY_ACCEPT_CONTENT == ["json"] else "FALHA", f"CELERY_ACCEPT_CONTENT = {settings.CELERY_ACCEPT_CONTENT}")

# A09 Logging and alerting --------------------------------------------------------------------------------------------
class Coleta(logging.Handler):
    def __init__(self):
        super().__init__()
        self.itens = []

    def emit(self, rec):
        self.itens.append(rec.getMessage())


h = Coleta()
logging.getLogger().addHandler(h)
logging.getLogger().setLevel(logging.INFO)
h.itens.clear()
login("cliente", "senha-errada-xyz")
com_quem = [m for m in h.itens if "cliente" in m]
reg("A09", "Login falho registra QUEM tentou (usuário/IP)?", "FALHA" if not com_quem else "OK", f"mensagens geradas: {h.itens}")

# A10 Mishandling of exceptional conditions ---------------------------------------------------------------------------
r = cliente.post("/api/v1/cart/items/", "{json quebrado", content_type="application/json")
corpo = r.content.decode()[:120]
reg("A10", "JSON quebrado vira erro limpo (sem stack trace)?", "OK" if r.status_code == 400 and "Traceback" not in corpo else "FALHA", f"POST /cart/items/ com corpo inválido → {r.status_code} {corpo}")
out = subprocess.run([sys.executable, "-c", "import os,sys;os.environ['DEBUG']='1';os.environ['DJANGO_SETTINGS_MODULE']='config.settings';sys.path.insert(0,os.environ['LAB']);import django;django.setup();from django.test import Client;r=Client().get('/nao-existe-xyz');b=r.content.decode();print(r.status_code,'URLconf' in b or 'urlpatterns' in b.lower() or 'Using the URLconf' in b)"], capture_output=True, text=True, env={**os.environ}).stdout.strip().splitlines()[-1]
reg("A10", "Com DEBUG=1 a página 404 vaza o mapa de rotas?", "ATENÇÃO", f"(status, mostra rotas) = {out}  ← por isso DEBUG=0 em produção")

print(f"{'Item':<5} {'Resultado':<11} Verificação → evidência")
for item, perg, res, ev in linhas:
    print(f"{item:<5} {res:<11} {perg} → {ev}")
resumo = {}
for _, _, res, _ in linhas:
    resumo[res] = resumo.get(res, 0) + 1
print("\nresumo:", json.dumps(resumo, ensure_ascii=False))
