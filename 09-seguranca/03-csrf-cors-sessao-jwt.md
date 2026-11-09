# 3. CSRF, CORS e sessão versus JWT

> ⏱️ ~1h30 · Módulo 9 · Pré-requisitos: [9.02](02-injection-xss.md), [6.11 (CORS)](../06-apis-rest/11-cors.md), [6.06 (JWT)](../06-apis-rest/06-autenticacao-token-jwt.md)

> ✅ **Verificação.** Tudo executado em 2026-11-08 no laboratório do MiniShop (Python 3.13, Django 5.2.19, simplejwt), em **modo produção** (`DEBUG=0`) e **somente contra o ambiente local**. **As saídas são reais.** Como na aula 02, o foco é **verificar as defesas**: o que o servidor aceita, o que recusa e por quê.

## 🎯 Objetivos
- Explicar o **CSRF**, por que ele depende de **cookies enviados automaticamente**, e como o Django o bloqueia
- Distinguir **CSRF** (escrita indevida), **CORS** (leitura entre origens) e **XSS** (script na página)
- Ler os atributos de cookie (`Secure`, `HttpOnly`, `SameSite`) e dizer o que cada um protege
- Comparar **sessão no servidor** e **JWT**, inclusive o que acontece no **logout**
- Decidir onde o front-end guarda o token e justificar

## 🤔 Por que isso importa
Esses três acrônimos são confundidos o tempo todo, inclusive em entrevistas: “CORS protege contra CSRF?” (não!), “JWT é mais seguro que sessão?” (depende), “posso guardar o token no `localStorage`?” (com riscos). Entender **quem envia a credencial, quem decide e quem lê a resposta** resolve a confusão.

## 💡 Intuição (explicação simples)
Pense num **crachá de acesso**.
- **Sessão com cookie** é um crachá que o **segurança anexa sozinho** em qualquer coisa que você entregue na portaria: se alguém convence você a entregar um papel malicioso, o crachá vai junto. É o **CSRF**: o navegador manda o cookie mesmo quando a requisição foi *provocada por outro site*. A cura é o **código secreto do formulário** (o token CSRF), que o site malicioso não consegue ver.
- **JWT no cabeçalho** é um crachá que **você precisa mostrar de propósito** em cada pedido: o navegador não o anexa sozinho, então não há CSRF. O custo: onde você **guarda** o crachá? Se um script malicioso (XSS) rodar na página, ele pode lê-lo.
- **CORS** é a regra da portaria sobre **quem pode ler as respostas** quando o pedido vem de outro prédio. Ela não impede o pedido de **sair**; impede o outro site de **ler** o que voltou.

## 🔬 Como funciona por dentro
- **CSRF (*Cross-Site Request Forgery*):** o navegador anexa **automaticamente** os cookies do domínio a qualquer requisição para ele, **inclusive as disparadas por outro site** (um formulário escondido, uma imagem). Se a rota autentica **só pelo cookie**, a ação acontece “como você”. Só vale para ações que **mudam estado** (POST/PUT/PATCH/DELETE); `GET` deve ser seguro (sem efeito colateral).
- **Defesas contra CSRF**, em camadas:
  1. **Token CSRF**: um valor imprevisível que o servidor coloca no formulário e **exige de volta**; o site malicioso não consegue lê-lo (a política de mesma origem impede).
  2. **`SameSite` no cookie**: `Lax` (padrão do Django) não envia o cookie em requisições *cross-site* que não sejam navegação segura (`GET` de topo); `Strict` é ainda mais restrito; `None` exige `Secure` e reabre o risco.
  3. **Conferência de `Origin`/`Referer`**: em HTTPS, o Django confere que a origem da requisição é confiável (`CSRF_TRUSTED_ORIGINS` quando houver outras).
  4. **Não usar cookie como credencial da API** (usar o cabeçalho `Authorization`).
- **Atributos do cookie:** `Secure` (só por HTTPS), `HttpOnly` (JavaScript **não** lê: reduz o estrago de um XSS), `SameSite` (limita o envio *cross-site*), `Max-Age`/`Expires`. O cookie do CSRF **não** é `HttpOnly` por padrão porque o JavaScript do site pode precisar lê-lo para enviar no cabeçalho.
- **CORS (*Cross-Origin Resource Sharing*):** o navegador aplica a **política de mesma origem**: um script de `a.com` não pode **ler** respostas de `b.com`. O CORS é a forma de `b.com` **liberar** origens específicas por cabeçalhos (`Access-Control-Allow-Origin`). **Não é um mecanismo de autenticação nem protege o servidor**: um `curl` ignora o CORS, e requisições “simples” (um formulário) **saem mesmo assim**. Ele protege os **dados do usuário no navegador** contra leitura por sites não autorizados. Nunca combine `Allow-Origin: *` com credenciais, e nunca **reflita** qualquer `Origin` recebido.
- **Sessão (servidor guarda o estado):** o cookie leva só um **identificador aleatório**; os dados ficam no servidor. **Revogar é imediato** (apagar a sessão). Custo: estado no servidor (banco/cache) e dependência do cookie (logo, CSRF).
- **JWT (cliente guarda o estado):** o token carrega as *claims* (`user_id`, `exp`…) e uma **assinatura**. O servidor só **verifica** a assinatura, sem consultar nada (bom para escalar). O payload é **legível por qualquer um** (só é base64, não é segredo!). O custo: **revogar antes de expirar é difícil**, daí o *access token* curto + *refresh token* com rotação e lista negra.
- **Onde guardar o token no navegador:**
  | Lugar | Risco principal | Observação |
  |---|---|---|
  | `localStorage` | qualquer XSS **lê** o token | simples, mas frágil |
  | memória (variável JS) | some ao recarregar a página | mais segura contra XSS persistente; usa-se *refresh* para recuperar |
  | cookie `HttpOnly` + `Secure` + `SameSite` | CSRF (volta o problema) | JS não lê; exige token CSRF |
  Não existe opção sem custo: escolha conscientemente e **reduza o XSS** (aula 02) em qualquer caso.
- **Armadilhas de JWT:** aceitar o algoritmo `none`, ou confundir algoritmos; chave fraca; *claims* sensíveis no payload; tokens longos demais.

## 🛠️ Exemplo prático
**1. Tudo numa verificação só** (`csrf_sessao_jwt.py`: usa a verificação CSRF ligada, lê os cookies e testa o servidor com tokens válidos, adulterados e sem assinatura)
```python
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
```
```bash
DEBUG=0 SECRET_KEY=... ALLOWED_HOSTS=testserver SECURE_SSL_REDIRECT=0 LAB=$PWD uv run python csrf_sessao_jwt.py
```
```text
== 1) CSRF numa rota que usa COOKIE de sessão (login do admin), com a verificação ligada
   POST sem token CSRF                    → 403  (403 = recusado pelo Django)
   POST com token CSRF + Referer válido   → 302  (302 = login aceito)
   token válido, mas Referer de OUTRO site → 403  (403: em HTTPS o Django confere o Referer/Origin)

== 2) Atributos dos cookies emitidos no login (DEBUG=0)
   csrftoken  Secure=True  HttpOnly=False SameSite=Lax
   sessionid  Secure=True  HttpOnly=True  SameSite=Lax

== 3) A API usa JWT no cabeçalho Authorization (o navegador NÃO o anexa sozinho)
   cabeçalho: {'alg': 'HS256', 'typ': 'JWT'}
   payload  : {'token_type': 'access', 'exp': 1794177700, 'iat': 1794176800, 'user_id': '3'} (qualquer um LÊ; o que ninguém faz é ASSINAR)
   validade do access: 900 s
   token válido → 200 · payload alterado (assinatura antiga) → 401 · algoritmo 'none' sem assinatura → 401

== 4) Logout: sessão x JWT
   logout (refresh vai para a lista negra) → 200; usar o refresh de novo → 401
   o ACCESS antigo continua valendo até expirar → 200  (é por isso que ele dura só 900 s)
   sessão: antes do logout → 200; depois (a sessão some NO SERVIDOR) → 302

== 5) CORS: quem pode LER respostas da API de outra origem
   preflight de http://127.0.0.1:8200            → 200  Allow-Origin='http://127.0.0.1:8200'  Allow-Credentials=None
   preflight de https://site-malicioso.example   → 200  Allow-Origin=None  Allow-Credentials=None
```

**2. Lendo cada bloco**
- **CSRF (bloco 1):** o `POST` sem token foi recusado (`403`); com o token e o `Referer` do próprio site, aceito (`302`); com o token válido mas vindo de **outro site**, recusado (`403`): em HTTPS o Django confere também a origem. Foram três barreiras independentes.
- **Cookies (bloco 2):** `sessionid` com `Secure`, `HttpOnly` e `SameSite=Lax`; `csrftoken` com `Secure` e `SameSite=Lax`, mas **sem** `HttpOnly` (por padrão, para o JavaScript poder ler). Os valores vieram da configuração de produção da aula 8.06 (`SESSION_COOKIE_SECURE` e `CSRF_COOKIE_SECURE`).
- **JWT (bloco 3):** o cabeçalho diz `HS256`; o payload mostra `user_id`, `iat`, `exp` e **qualquer um o lê**. Validade do *access*: **900 s (15 min)**. O servidor aceitou o token íntegro (`200`) e **recusou** o de payload alterado com a assinatura antiga (`401`) e o `alg: none` sem assinatura (`401`).
- **Logout (bloco 4):** o logout põe o *refresh* na lista negra (reutilizá-lo → `401`), **mas o *access* antigo continuou valendo (`200`) até expirar**: é uma propriedade real do JWT, e é por isso que o *access* é curto. Na sessão, ao deslogar, a sessão **some no servidor** e o acesso seguinte é redirecionado ao login (`302`).
- **CORS (bloco 5):** o *preflight* de `http://127.0.0.1:8200` (origem permitida) devolveu `Allow-Origin` com essa origem; o de `https://site-malicioso.example` voltou **sem** `Allow-Origin`, então o navegador **não entrega a resposta** ao script daquele site. `Allow-Credentials` não é enviado (a API usa JWT no cabeçalho, sem cookies entre origens).

**3. Testes de regressão** (`tests/test_sessao_csrf_jwt.py`): `POST` sem token CSRF → `403`; com token → `302`; JWT com payload alterado → `401`; JWT `alg: none` → `401`; *access* com vida de no máximo 15 min; cookies de sessão com `HttpOnly` e `SameSite`:
```text
6 passed
```
Somados ao `test_cors.py` do módulo 6, o laboratório fecha com a suíte inteira verde (veja o fim da aula 06).

**4. Sessão ou JWT? Quando usar cada um**
| Critério | Sessão (cookie) | JWT (cabeçalho) |
|---|---|---|
| Revogação | **imediata** | só ao expirar (ou lista negra) |
| Estado no servidor | sim | não (exceto refresh/lista negra) |
| CSRF | **precisa** de proteção | não se aplica (sem cookie) |
| XSS lê a credencial? | `HttpOnly`: não | `localStorage`: sim; memória: durante a página |
| Vários clientes (app móvel, terceiros) | incômodo | natural |
| Site renderizado no servidor (Django templates) | **a escolha natural** | complica |
| API pública para SPAs/apps | possível, com cuidado | comum |
Regra prática: **site tradicional → sessão**; **API consumida por apps e SPAs → JWT curto + refresh com rotação**; e **nunca misture** sem entender o CSRF do cookie.

**5. O `csrf_exempt` do webhook, revisitado.** O guarda da aula 02 só deixa `csrf_exempt` em `apps/payments/api.py`. É justificado: o webhook **não usa cookie** (o provedor não tem sessão do seu site), e a autenticação é a **assinatura HMAC** do corpo (aula 7.09). Isentar do CSRF uma rota autenticada **por cookie** seria uma falha grave.

## 🧠 Pausa para lógica
**Problema.** Um colega diz: “Já temos CORS configurado só para o nosso front-end, então ninguém consegue disparar um `POST` para a nossa API a partir de outro site.” Ele está certo? Explique com o que o navegador faz com formulários simples e com `fetch` com JSON e `Authorization`.

<details><summary>Dica</summary>O CORS decide quem pode <em>ler</em> a resposta; o navegador exige <em>preflight</em> só para requisições “não simples”.</details>

<details><summary>Solução comentada</summary>

**Não está certo.** Um `<form method="post">` ou um `fetch` “simples” (`Content-Type` de formulário) **sai sem preflight**, o servidor **recebe e executa**, e o CORS apenas impede o site malicioso de **ler a resposta**. Isso é exatamente o CSRF, e por isso o cookie precisa de token CSRF/`SameSite`. Já um `fetch` com JSON e o cabeçalho `Authorization` exige *preflight*; o navegador só envia o `POST` se o servidor autorizar a origem. Na nossa API isso ajuda **porque** a credencial é o cabeçalho (que o site malicioso não consegue anexar), não por causa do CORS em si. E fora do navegador (curl, scripts) o CORS não protege nada: **a autorização no servidor é a defesa**.
</details>

## ⚠️ Erros comuns e boas práticas
| Sintoma | Causa | Solução |
|---|---|---|
| “CORS protege a API” | Confundir com autenticação | CORS controla leitura no navegador; autorize no servidor |
| `Access-Control-Allow-Origin: *` com credenciais | Atalho para “funcionar” | Lista explícita de origens; sem curinga com credenciais |
| Servidor reflete o `Origin` recebido | “Liberar todo mundo” disfarçado | Comparar com uma lista fixa |
| `csrf_exempt` em rota com cookie | Erro para “resolver” um 403 | Enviar o token CSRF; manter a proteção |
| `GET` que muda estado | Ignorar a semântica HTTP | `POST`/`DELETE` para efeitos colaterais |
| JWT em `localStorage` com XSS aberto | Credencial legível por script | Reduzir XSS, CSP; token curto; considerar memória ou cookie `HttpOnly` |
| Segredo ou dado sensível no payload do JWT | “Está assinado” | O payload é legível; só identificadores e *claims* necessárias |
| *Access token* de 30 dias | Conveniência | 5–15 min + refresh com rotação |
| Aceitar qualquer algoritmo no JWT | Configuração permissiva | Fixar o algoritmo e a chave; recusar `none` (a biblioteca já o faz) |
| Cookie de sessão sem `Secure` em produção | Esquecer HTTPS | `SESSION_COOKIE_SECURE`/`CSRF_COOKIE_SECURE` (aula 8.06) |

- **`Lax` por padrão;** use `None` só com necessidade real e com `Secure`.
- **Logout completo** = apagar o estado no cliente **e** invalidar o que for possível no servidor.
- **Revisite as origens permitidas** a cada novo front-end.

## 🧩 Exercícios
**1. Fixação.** (a) Por que o CSRF só afeta autenticação por cookie? (b) O que o `SameSite=Lax` impede? (c) Por que o payload de um JWT não deve conter segredos? (d) Por que o logout não invalida imediatamente o *access token*?

<details><summary>Solução</summary>

(a) Porque o navegador anexa cookies sozinho, inclusive em requisições provocadas por outros sites; um cabeçalho `Authorization` precisa ser anexado pelo código do próprio site. (b) Impede o envio do cookie em requisições *cross-site* que não sejam navegação de topo segura (por exemplo, um `POST` vindo de um formulário em outro site). (c) Porque é só base64: qualquer um decodifica; a assinatura garante integridade, não sigilo. (d) Porque o servidor não consulta estado para validar o *access*; ele vale até o `exp`, daí a vida curta e o *refresh* na lista negra.
</details>

**2. Aplicação no projeto MiniShop.**
- [ ] Documentar em `docs/seguranca.md` a decisão **JWT (API) + sessão (admin)** e por que o CSRF só vale para o admin
- [ ] Testes: CSRF no admin (`403` sem token), JWT adulterado e `alg: none` (`401`), vida do *access* ≤ 15 min, atributos dos cookies
- [ ] Conferir `CORS_ALLOWED_ORIGINS` por ambiente (sem `*`, sem refletir `Origin`) com teste
- [ ] Tabela do front-end: onde o token fica (memória + refresh) e por quê
- [ ] Revisar o `csrf_exempt` do webhook com a justificativa escrita
- [ ] Commit `test(security): csrf, cookie flags and jwt tampering`

**3. Desafio (opcional).** Faça o painel de administração aceitar apenas `SameSite=Strict` e descreva o que quebra na experiência (por exemplo, links vindos de e-mail para o admin) e como contornar.

## 🎤 Na entrevista
- **O que é CSRF e como se previne?** Uma ação indesejada disparada por outro site aproveitando que o navegador anexa o cookie sozinho; previne-se com token CSRF, `SameSite`, conferência de origem e usando o cabeçalho `Authorization` em vez de cookie.
- **O CORS protege contra CSRF?** Não. O CORS controla quem pode *ler* respostas entre origens no navegador; o `POST` simples sai e é executado do mesmo jeito.
- **Sessão ou JWT?** Sessão: revogação imediata e cookie `HttpOnly`, mas estado no servidor e CSRF; JWT: sem estado e bom para vários clientes, mas revogar é difícil, então usa-se *access* curto e *refresh* com rotação.
- **Onde guardar o JWT no navegador?** Não há opção sem risco: `localStorage` é legível por XSS; memória some ao recarregar; cookie `HttpOnly` volta o CSRF. Reduza o XSS e escolha conscientemente.
- **O que significam `Secure`, `HttpOnly` e `SameSite`?** Só HTTPS; inacessível ao JavaScript; limita o envio em requisições entre sites.

## 📚 Para ir além
- 📄 Documentação oficial: [Django — CSRF](https://docs.djangoproject.com/en/5.2/howto/csrf/). Token, `SameSite` e origens confiáveis.
- 📄 Documentação oficial: [Django — Sessões](https://docs.djangoproject.com/en/5.2/topics/http/sessions/). Armazenamento e ciclo de vida.
- 📄 Guia: [OWASP — CSRF Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html). Defesas em camadas (em inglês).
- 📄 Guia: [OWASP — Session Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html). Cookies e ciclo de vida (em inglês).
- 📄 Referência: [MDN — CORS](https://developer.mozilla.org/pt-BR/docs/Web/HTTP/Guides/CORS). Preflight e cabeçalhos.
- 📄 Referência: [MDN — Cookies](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Cookies). `Secure`, `HttpOnly`, `SameSite` (em inglês).
- 📄 Norma: [RFC 8725 — JWT Best Current Practices](https://datatracker.ietf.org/doc/html/rfc8725). Armadilhas e boas práticas (em inglês).
- 📄 Documentação: [Simple JWT](https://django-rest-framework-simplejwt.readthedocs.io/en/latest/). Rotação e lista negra (em inglês).

## ✅ Checklist da aula
- [ ] Sei explicar por que o CSRF depende de cookies automáticos
- [ ] Diferencio CSRF, CORS e XSS (quem envia, quem lê, quem executa)
- [ ] Li os atributos `Secure`, `HttpOnly` e `SameSite` dos cookies do MiniShop
- [ ] Sei o que o logout invalida (e o que não invalida) em sessão e em JWT
- [ ] Justifiquei por escrito onde o token fica no front-end
