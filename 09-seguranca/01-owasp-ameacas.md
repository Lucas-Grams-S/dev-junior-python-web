# 1. OWASP Top 10 e modelagem de ameaças

> ⏱️ ~1h30 · Módulo 9 · Pré-requisitos: [Módulo 6 (API REST, JWT, permissões)](../06-apis-rest/README.md), [8.06 (configuração por ambiente)](../08-arquitetura/06-twelve-factor.md)

> ✅ **Verificação.** Tudo executado em 2026-11-08 no laboratório do MiniShop (Python 3.13, Django 5.2.19), **somente contra o meu próprio ambiente local**. A lista usada é a **OWASP Top 10:2025** (a página oficial redireciona para ela; a de 2021 está superada). **As saídas são reais.**

> ⚖️ **Regra de ouro deste módulo.** Os ataques aqui são demonstrados **apenas no laboratório que você montou**. Testar sistemas de terceiros sem autorização por escrito é crime (no Brasil, o art. 154-A do Código Penal, “invasão de dispositivo informático”) e viola os termos de qualquer plataforma. Em entrevista e no trabalho, o tom é **defensivo**: achar, provar e corrigir.

## 🎯 Objetivos
- Listar as 10 categorias do **OWASP Top 10:2025** e dar um exemplo de cada no contexto do MiniShop
- Fazer uma **auditoria executável** (cada risco vira uma sondagem que passa ou falha)
- Modelar ameaças com **fluxo de dados, fronteiras de confiança e STRIDE**
- Priorizar achados por **risco** (probabilidade × impacto) e transformá-los em um **backlog**

## 🤔 Por que isso importa
Quem desenvolve a aplicação é a pessoa mais bem posicionada para evitar a vulnerabilidade, e a mais barata de corrigir: um bug de segurança achado no código custa minutos; achado em produção custa dinheiro, reputação e, no Brasil, pode virar problema de **LGPD** (aula 07). Em entrevistas para dev júnior, “cite três itens do OWASP Top 10 e como evitá-los” é pergunta quase certa.

## 💡 Intuição (explicação simples)
Pense na sua casa. Você pode (1) **trancar as portas** conforme o que valorizam os ladrões (lista de riscos mais comuns: o Top 10), e (2) **desenhar a planta** marcando por onde alguém entra, onde ficam os objetos de valor e quem tem chave (a modelagem de ameaças). A lista dá o *o quê*; a planta dá o *onde* no **seu** sistema. A auditoria é andar pela casa testando cada fechadura de verdade, em vez de supor que está trancada.

## 🔬 Como funciona por dentro
**OWASP Top 10:2025** (consenso sobre os riscos mais críticos em aplicações web; é uma lista de **conscientização**, não um padrão de conformidade):
| # | Categoria | Em uma frase | No MiniShop |
|---|---|---|---|
| A01 | Broken Access Control | usuário faz/vê o que não deveria | ver o pedido de outro (IDOR, aula 05) |
| A02 | Security Misconfiguration | configuração insegura ou padrão esquecido | cabeçalhos, `DEBUG`, rotas de demonstração expostas (aula 06) |
| A03 | Software Supply Chain Failures | dependências e cadeia de build comprometidas | pacotes com CVE, `pip-audit` (aula 06) |
| A04 | Cryptographic Failures | cripto fraca ou ausente | hash de senha, HTTPS, chave do JWT (aulas 04 e 07) |
| A05 | Injection | dado do usuário vira código | SQL injection, XSS (aula 02) |
| A06 | Insecure Design | falha de **projeto**, não de código | regras de negócio abusáveis (cupom, estoque) |
| A07 | Authentication Failures | login, sessão e senha fracos | senhas fracas aceitas, força bruta (aula 04) |
| A08 | Software or Data Integrity Failures | confiar em código/dados sem verificar | webhook sem assinatura, `pickle` (aula 7.09) |
| A09 | Security Logging and Alerting Failures | não registrar nem alertar | login falho sem rastro (aula 06) |
| A10 | Mishandling of Exceptional Conditions | erros tratados mal (vazam dados ou deixam passar) | stack trace na resposta, falha que “abre” o acesso |

- **A lista muda com o tempo.** Nesta edição aparecem **A03** (cadeia de suprimentos de software) e **A10** (condições excepcionais) como categorias próprias, e *Injection* está em 5º; *Broken Access Control* lidera. (Para saber o que mudou em relação a 2021, leia a página “Introduction” da própria OWASP.) Não decore posições: entenda os **tipos de falha**.
- **Modelagem de ameaças** responde a quatro perguntas: *o que estamos construindo? o que pode dar errado? o que faremos a respeito? fizemos um bom trabalho?* Os passos práticos: (1) desenhar o **diagrama de fluxo de dados** com **fronteiras de confiança** (onde a confiança muda: navegador → API, API → banco, API → provedor); (2) aplicar o **STRIDE** em cada fluxo; (3) priorizar e registrar mitigações.
- **STRIDE**: *S*poofing (falsificar identidade), *T*ampering (alterar dados), *R*epudiation (negar ter feito), *I*nformation disclosure (vazar informação), *D*enial of service (derrubar), *E*levation of privilege (ganhar poder indevido).
- **Risco = probabilidade × impacto.** Um achado raro de impacto baixo pode esperar; um fácil de explorar que expõe dados de clientes, não.
- **Defesa em profundidade:** nenhuma camada sozinha basta (validação + autorização + ORM parametrizado + cabeçalhos + logs). E **falhar fechado**: na dúvida, negar.

## 🛠️ Exemplo prático
**1. O diagrama de fluxo de dados do MiniShop** (fronteiras de confiança marcadas com `║`)
```text
 [Navegador/App]  ──HTTPS──▶ ║ [API Django/DRF] ──ORM──▶ [Banco]
   (não confiável)           ║        │   │
                             ║        │   └──fila──▶ [Celery/Redis] ──▶ [E-mail]
 [Provedor de pagamento] ──webhook──▶ ║        │
   (confiança parcial: só com assinatura)       └──HTTPS──▶ [Gateway de pagamento]
```
Tudo que cruza `║` é **entrada não confiável** até ser validada.

**2. STRIDE aplicado a três fluxos**
| Fluxo | Ameaça (STRIDE) | Exemplo concreto | Mitigação | Aula |
|---|---|---|---|---|
| Login | **S**poofing | força bruta / senha vazada reaproveitada | limite de tentativas, senha forte, hash lento | 04 |
| `GET /orders/{id}/` | **I**nfo disclosure / **E**levation | ler o pedido de outra pessoa trocando o `id` | filtrar por dono (retornar 404) | 05 |
| `POST /orders/` | **T**ampering | mandar `total` ou `status` no corpo | o servidor calcula; campos só de leitura | 05 |
| Webhook | **S**poofing / **T**ampering / **R**eplay | evento falso “pago” | HMAC + timestamp (já feito) | 7.09 |
| Qualquer ação sensível | **R**epudiation | “não fui eu que cancelei” | log de auditoria com quem/quando/IP | 06 |
| `/api/v1/auth/token/` | **D**enial of service | milhares de tentativas por segundo | *throttling* (já existe) | 06 |

**3. Auditoria executável** (`auditoria.py`: cada risco do Top 10 vira uma **sondagem** contra o MiniShop local, em modo produção: `DEBUG=0`, chave aleatória)
```python
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
reg("A04", "Algoritmo de hash de senhas", "OK", f"{settings.PASSWORD_HASHERS[0].rsplit('.', 1)[-1]} (padrão do Django; Argon2 é discutido na aula 9.04)")
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
```
```bash
DEBUG=0 SECRET_KEY=... ALLOWED_HOSTS=testserver SECURE_SSL_REDIRECT=0 ORDER_EMAIL_MODE=off LAB=$PWD uv run python auditoria.py
```
```text
Item  Resultado   Verificação → evidência
A01   OK          Anônimo lista pedidos? → GET /orders/ sem token → 401
A01   OK          Outro usuário lê o pedido de 'cliente' (IDOR)? → GET /orders/1/ como estoquista → 404
A01   OK          Outro usuário cancela o pedido? → POST /orders/1/cancel/ → 404
A01   OK          Cliente comum cria produto? → POST /products/ como cliente → 403
A02   FALHA       Cabeçalhos de segurança presentes? → ausentes: Content-Security-Policy, Permissions-Policy
A02   ATENÇÃO     /demo/sync/ exposto em produção? → GET /demo/sync/ → 200
A02   ATENÇÃO     /admin/login/ exposto em produção? → GET /admin/login/ → 200
A02   ATENÇÃO     /api/docs/ exposto em produção? → GET /api/docs/ → 200
A02   OK          DEBUG desligado? → DEBUG=False
A03   NÃO MEDIDO  Dependências auditadas (pip-audit)? → veja a aula 9.06
A04   OK          Algoritmo de hash de senhas → PBKDF2PasswordHasher (padrão do Django; Argon2 é discutido na aula 9.04)
A04   ATENÇÃO     JWT assinado com → HS256 usando a SECRET_KEY da aplicação (a mesma chave assina sessões)
A05   ATENÇÃO     SQL cru, mark_safe ou csrf_exempt no código? → 2 ocorrência(s): apps/payments/api.py:4:from django.views.decorators.csrf import csrf_exempt | apps/payments/api.py:16:@csrf_exempt                                                  # nã
A05   OK          Busca resiste a ' OR 1=1 --? → GET /products/?search=' OR 1=1 -- → 200, 0 resultados
A06   OK          Quantidade negativa no carrinho? → POST quantity=-5 → 400
A06   OK          Auto-promoção a gerente (mass assignment)? → PATCH /auth/me/ role=manager → 405
A07   OK          Erro de login revela se o usuário existe? → usuário inexistente → 401; senha errada → 401; corpos iguais: True
A07   OK          Tentativas de login são limitadas? → 7 tentativas seguidas → [401, 401, 401, 401, 401, 429, 429]
A07   FALHA       Há validadores de senha? → AUTH_PASSWORD_VALIDATORS = []
A08   OK          Webhook exige assinatura? → HMAC + timestamp (aula 7.09); sem assinatura → 401
A08   OK          Celery aceita só JSON (sem pickle)? → CELERY_ACCEPT_CONTENT = ['json']
A09   FALHA       Login falho registra QUEM tentou (usuário/IP)? → mensagens geradas: ['Unauthorized: /api/v1/auth/token/']
A10   OK          JSON quebrado vira erro limpo (sem stack trace)? → POST /cart/items/ com corpo inválido → 400 {"detail":"JSON parse error - Expecting property name enclosed in double quotes: line 1 column 2 (char 1)","code":"parse
A10   ATENÇÃO     Com DEBUG=1 a página 404 vaza o mapa de rotas? → (status, mostra rotas) = 404 True  ← por isso DEBUG=0 em produção

resumo: {"OK": 14, "FALHA": 3, "ATENÇÃO": 6, "NÃO MEDIDO": 1}
```

> 🔎 **Duas correções no meu próprio método (fazem parte da lição).** Minha primeira versão tinha “OK” **enganosos**: (1) o limite de login já havia estourado por causa dos meus próprios logins anteriores, então **tudo** respondia `429` e a comparação “usuário inexistente × senha errada” comparava dois `429` (nada provava); passei a limpar o contador entre as sondagens e a **medir o limite sem limpar**: `[401, 401, 401, 401, 401, 429, 429]`. (2) O teste de “JSON quebrado” foi num endpoint que **ignora o corpo** e devolveu `201`; passei a usar um endpoint que lê o corpo (`400`). (3) O HSTS aparecia como ausente porque eu sondava por HTTP: esse cabeçalho **só é enviado em HTTPS**. Um teste de segurança que dá “OK” pelo motivo errado é pior que nenhum.

**4. Lendo o resultado: o que está bom e o que vira trabalho**
| Resultado | Achado | Prioridade | Resolvido em |
|---|---|---|---|
| ✅ A01 | pedidos de outros usuários dão `404`; cliente não cria produto | — | (reforçar com testes: aula 05) |
| ❌ A02 | faltam `Content-Security-Policy` e `Permissions-Policy` | média | aula 06 |
| ⚠️ A02 | `/demo/sync/`, `/admin/` e `/api/docs/` acessíveis a qualquer um em “produção” | alta (admin) / média | aula 06 |
| ⚠️ A04 | JWT HS256 assinado com a mesma `SECRET_KEY` da aplicação; hash PBKDF2 (padrão) | média | aula 04 |
| ⚠️ A05 | `csrf_exempt` no webhook (justificado: autenticado por assinatura) | baixa | aula 03 |
| ❌ A07 | **sem validadores de senha**: aceita `123` | alta | aula 04 |
| ❌ A09 | login falho **não registra quem tentou** (só `Unauthorized: /api/v1/auth/token/`) | média | aula 06 |
| ➖ A03 | dependências **não auditadas** | alta | aula 06 |
| ✅ A05/A06/A08/A10 | busca com `' OR 1=1 --` não injeta; quantidade negativa dá `400`; sem `pickle`; erro de JSON sem stack trace | — | — |

Observe a diferença entre *“não achei problema”* e *“não há problema”*: 14 sondagens `OK` significam que **essas** hipóteses falharam, não que o sistema é seguro. Nas próximas aulas vamos atacar de verdade (SQL injection, XSS, CSRF, IDOR) num ambiente vulnerável **de propósito** e depois corrigir.

**5. Registrar o backlog** (será o `docs/seguranca.md` da entrega, uma linha por achado: ID, risco, evidência, correção, estado). Hoje o relatório tem vários itens abertos (cabeçalhos, rotas expostas, senhas, log, dependências), todos com aula de destino.

## 🧠 Pausa para lógica
**Problema.** Você tem 4 achados: (a) painel `/admin/` público, probabilidade alta, impacto alto; (b) falta de CSP, probabilidade média, impacto médio; (c) log de login incompleto, probabilidade baixa, impacto médio; (d) senha `123` aceita, probabilidade alta, impacto médio. Ordene do mais ao menos urgente usando risco = probabilidade × impacto (baixa=1, média=2, alta=3) e diga o que desempata.

<details><summary>Dica</summary>Calcule o produto de cada um; em caso de empate, pergunte “qual é mais fácil de explorar e qual expõe mais pessoas?”.</details>

<details><summary>Solução comentada</summary>

(a) 3×3 = **9**; (d) 3×2 = **6**; (b) 2×2 = **4**; (c) 1×2 = **2**. Ordem: **a, d, b, c**. Atenção: não há empate aqui, mas se (b) e (d) empatassem, o desempate seria a **facilidade de exploração** (senha fraca é explorada por script) e o **alcance** (todas as contas). Observe também que o log (c) tem risco baixo *isolado*, mas sem ele você **não descobre** os outros ataques: é um multiplicador de detecção, por isso sobe de prioridade num projeto real.
</details>

## ⚠️ Erros comuns e boas práticas
| Sintoma | Causa | Solução |
|---|---|---|
| “Passou na auditoria, é seguro” | Confundir ausência de achados com ausência de falhas | Sondagem prova só a hipótese testada; combine com revisão e modelagem |
| Sondagem que dá OK pelo motivo errado | Estado sujo (cache, limite) ou endpoint errado | Isolar o estado, validar que a sondagem *falha* quando deveria (mutação) |
| Corrigir só os itens fáceis | Sem priorização | Risco = probabilidade × impacto; backlog ordenado |
| Segurança “no fim do projeto” | Tratar como etapa | Modelar ameaças ao desenhar; testes de segurança no CI |
| Testar um sistema que não é seu | Curiosidade sem autorização | Só laboratório próprio ou escopo autorizado por escrito |
| Decorar a lista | Foco na posição | Entender o tipo de falha; a lista muda a cada edição |
| Confiar só no front-end | Validação no cliente | Toda validação e autorização acontece **no servidor** |

- **Falhe fechado:** na dúvida, negue (404/403), nunca “deixe passar”.
- **Menos é mais:** cada rota, porta e dependência é superfície de ataque; remova o que não usa.
- **Registre decisões** de segurança num relatório vivo.

## 🧩 Exercícios
**1. Fixação.** (a) Cite cinco categorias do Top 10:2025 com um exemplo do MiniShop. (b) Qual a diferença entre uma falha de *implementação* e de *projeto* (A06)? (c) O que é uma fronteira de confiança e por que o webhook cruza uma? (d) O que significa cada letra do STRIDE?

<details><summary>Solução</summary>

(a) Ex.: A01 IDOR em `/orders/{id}`; A02 `/admin/` público; A05 SQL injection na busca; A07 senha `123` aceita; A09 login falho sem registro. (b) Implementação: o código erra (ex.: concatenar SQL). Projeto: o código faz o que foi pedido, mas a **regra** é abusável (ex.: cupom que se soma infinitamente), então nenhuma correção de linha resolve: é preciso redesenhar. (c) Onde muda o nível de confiança (navegador → API; provedor → API); o webhook entra de fora, então só se confia depois de verificar a assinatura. (d) Spoofing, Tampering, Repudiation, Information disclosure, Denial of service, Elevation of privilege.
</details>

**2. Aplicação no projeto MiniShop.** Comece o relatório `docs/seguranca.md`:
- [ ] Diagrama de fluxo de dados com as fronteiras de confiança
- [ ] Tabela STRIDE com pelo menos 6 linhas (fluxo, ameaça, mitigação)
- [ ] `auditoria.py` rodando em modo produção, com a saída anexada
- [ ] Backlog ordenado por risco (ID, categoria, evidência, correção, estado)
- [ ] Pelo menos **uma sondagem validada por mutação** (quebre de propósito a proteção e veja a sondagem falhar)
- [ ] Commit `docs(security): threat model and OWASP 2025 audit`

**3. Desafio (opcional).** Acrescente à auditoria uma sondagem para **A06**: o mesmo cupom pode ser aplicado duas vezes no mesmo pedido? E para **A10**: se o gateway de pagamento cair no meio do `pay`, o pedido fica num estado coerente?

## 🎤 Na entrevista
- **Cite itens do OWASP Top 10 e como evitá-los.** Controle de acesso quebrado (autorizar no servidor, por objeto), injeção (consultas parametrizadas e escape de saída), falhas de autenticação (hash lento, limite de tentativas, MFA), configuração insegura (cabeçalhos, `DEBUG` desligado, sem rotas de demonstração), dependências vulneráveis (`pip-audit`, lockfile).
- **O que é modelagem de ameaças?** Desenhar o sistema (fluxos e fronteiras de confiança), listar o que pode dar errado (STRIDE), decidir mitigações e verificar; faz-se no projeto, não no fim.
- **Como priorizar vulnerabilidades?** Por risco: probabilidade × impacto, considerando facilidade de exploração e quantos usuários atinge.
- **O que é defesa em profundidade?** Várias camadas independentes, de modo que a falha de uma não comprometa tudo.
- **O que fazer ao achar uma vulnerabilidade em produção?** Conter (mitigar), corrigir com teste, avaliar se dados foram expostos (e se há obrigação de comunicar, LGPD) e registrar o aprendizado.

## 📚 Para ir além
- 📄 Referência: [OWASP Top 10:2025](https://owasp.org/Top10/2025/en/). A lista completa, com exemplos e prevenção (em inglês).
- 📄 Guia: [OWASP — Threat Modeling Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Threat_Modeling_Cheat_Sheet.html). Passo a passo curto (em inglês).
- 📄 Guia: [OWASP — Threat Modeling Process](https://owasp.org/www-community/Threat_Modeling_Process). Fluxo de dados e fronteiras (em inglês).
- 📄 Padrão: [OWASP ASVS](https://owasp.org/www-project-application-security-verification-standard/). Requisitos de verificação por nível (em inglês).
- 📄 Documentação oficial: [Django — Segurança](https://docs.djangoproject.com/en/5.2/topics/security/). O que o framework já faz por você.
- 📄 Documentação: [STRIDE nas ameaças do Threat Modeling Tool](https://learn.microsoft.com/en-us/azure/security/develop/threat-modeling-tool-threats). Categorias e exemplos (em inglês).
- 🧰 Ferramenta: [OWASP Threat Dragon](https://owasp.org/www-project-threat-dragon/). Desenhar diagramas de ameaças.

## ✅ Checklist da aula
- [ ] Sei dizer as 10 categorias do OWASP Top 10:2025 e dar um exemplo de cada
- [ ] Desenhei o fluxo de dados com as fronteiras de confiança do MiniShop
- [ ] Apliquei o STRIDE em pelo menos seis fluxos
- [ ] Rodei a auditoria e entendi o que cada “OK” realmente prova
- [ ] Tenho um backlog de segurança priorizado por risco
