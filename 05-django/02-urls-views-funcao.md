# 02. URLs e views baseadas em função

> ⏱️ ~1h30 · Módulo 5 · Pré-requisitos: [01](01-projeto-apps-mvt.md); HTTP ([2.02](../02-como-a-web-funciona/02-http-metodos-status-headers.md)) e o roteador da [aula 2.05](../02-como-a-web-funciona/05-servidor-http-minimo.md)

## 🎯 Objetivos
Ao final desta aula você consegue:
- Mapear URLs para *views* com `path()`, *converters* (`<int:pk>`, `<slug:slug>`) e `include()`
- Usar `name`/`app_name` e `reverse()`/`resolve()` em vez de escrever URLs “na mão”
- Escrever *views* de função que leem o `HttpRequest` (método, query string, corpo, cabeçalhos) e devolvem `HttpResponse`, `JsonResponse`, redirecionamentos e `404`
- Restringir métodos HTTP com decorators e explicar o **CSRF** (por que um `POST` sem token leva `403`)
- Testar *views* com o cliente de testes do Django e o pytest

## 🤔 Por que isso importa
URLs e *views* são a “porta de entrada” de tudo no Django: toda tela, toda API e todo *webhook* começa em uma função que recebe uma requisição e devolve uma resposta. É também o ponto onde você aplica o que aprendeu em HTTP: método certo, status certo, e o erro certo (`404`, `405`, `403`).

## 💡 Intuição (explicação simples)
A **tabela de URLs** é o **quadro de ramais da recepção**: “produtos → ramal do catálogo, carrinho → ramal do caixa”. A **view** é a **pessoa que atende o ramal**: ouve o pedido (a requisição), faz o que for preciso e devolve uma resposta educada com o código certo (“aqui está”, “não existe”, “você não pode”). E o `reverse()` é **discar pelo nome da pessoa**, não pelo número: se o ramal mudar, a agenda se atualiza sozinha.

## 🔬 Como funciona por dentro
**Resolução de URLs.** O Django lê `ROOT_URLCONF` (`config/urls.py`), percorre a lista `urlpatterns` **em ordem** e usa a **primeira** rota que casa com o caminho. `path("produtos/<slug:slug>/", detalhe, name="detail")` compara o caminho **sem** a `/` inicial; cada `<converter:nome>` captura um pedaço e o entrega à *view* como argumento nomeado.

| Converter | Casa com | Exemplo |
|---|---|---|
| `str` (padrão) | texto sem `/` | `<str:nome>` |
| `int` | inteiro ≥ 0 | `<int:pk>` → `42` |
| `slug` | letras, números, `-` e `_` | `<slug:slug>` → `mouse-sem-fio` |
| `uuid` | UUID | `<uuid:token>` |
| `path` | texto **com** `/` | `<path:arquivo>` |

- **`include("apps.catalog.urls")`** delega um prefixo a outro `urls.py` (cada app cuida das suas rotas).
- **`name` e `app_name`:** dão **nomes** às rotas (`catalog:detail`). Em código use `reverse("catalog:detail", kwargs={"slug": ...})`; em *templates*, `{% url 'catalog:detail' slug=p.slug %}`. Assim, mudar `produtos/` para `loja/` não quebra nenhum link.
- **`APPEND_SLASH`** (padrão): se `/produtos` não casa mas `/produtos/` casa, o Django responde `301` redirecionando para a versão com barra.
- **Ordem importa:** rotas mais específicas antes das genéricas (como no roteador da aula 2.05).

**A view de função.** É uma função Python que recebe um `HttpRequest` (`request`) e **devolve** um `HttpResponse` (ou lança uma exceção que vira resposta, como `Http404`).

| Em `request` | O que é |
|---|---|
| `request.method` | `"GET"`, `"POST"`… |
| `request.GET` / `request.POST` | `QueryDict` (query string / corpo de formulário); valores repetidos: `getlist()` |
| `request.body` | bytes do corpo (para JSON: `json.loads(request.body)`) |
| `request.headers` | cabeçalhos (insensível a maiúsculas) · `request.META` (ambiente WSGI) |
| `request.COOKIES`, `request.session`, `request.user` | preenchidos pelos *middlewares* (aulas 1, 11) |
| `request.path`, `request.get_full_path()` | caminho e caminho com query |

**Respostas:** `HttpResponse(texto, status=…, content_type=…)`, `JsonResponse(dict)`, `redirect("catalog:list")` (302; `permanent=True` para 301), `Http404` e `get_object_or_404` (aula 4+), `HttpResponseNotAllowed` (405), `HttpResponseBadRequest` (400). **O status certo** (aula 2.02) vale em Django como em qualquer lugar.

**Decorators úteis** (aula 1.16 em ação): `@require_GET`, `@require_POST`, `@require_http_methods(["GET", "POST"])` (devolvem `405` com `Allow`), `@csrf_exempt`, `@login_required` (aula 11).

**CSRF (*Cross-Site Request Forgery*).** O navegador envia cookies automaticamente, então um site malicioso poderia fazer o seu navegador logado **enviar um `POST`** ao MiniShop. O `CsrfViewMiddleware` exige, em requisições que alteram dados (`POST`, `PUT`, `PATCH`, `DELETE`), um **token secreto** que só páginas do próprio site conhecem (no formulário: `{% csrf_token %}`; em *fetch*: cabeçalho `X-CSRFToken`). Sem ele: `403 Forbidden`. `@csrf_exempt` desliga a proteção e **deve ser raro** (ex.: *webhooks* autenticados por assinatura, Módulo 7).

## 🛠️ Exemplo prático
Continuamos o projeto da aula 01. Como ainda não vimos *models* (aula 04) nem *templates* (aula 03), os dados vêm de uma lista em Python, **de propósito transitória**; as URLs e *views* que escrevemos aqui ficam.

**1. Dados provisórios e a primeira view**
```python
"""Dados PROVISÓRIOS (a aula 04 troca isto pelo banco)."""
PRODUTOS = [
    {"slug": "mouse-sem-fio", "nome": "Mouse sem fio", "preco": "89.90", "categoria": "perifericos", "estoque": 12},
    {"slug": "teclado-mecanico", "nome": "Teclado mecânico", "preco": "329.00", "categoria": "perifericos", "estoque": 5},
    {"slug": "fone-bluetooth", "nome": "Fone Bluetooth", "preco": "249.90", "categoria": "audio", "estoque": 3},
    {"slug": "soundbar", "nome": "Soundbar", "preco": "449.90", "categoria": "audio", "estoque": 0},
    {"slug": "monitor-27-4k", "nome": 'Monitor 27" 4K', "preco": "2199.00", "categoria": "monitores", "estoque": 5},
    {"slug": "cabo-hdmi-2m", "nome": "Cabo HDMI 2m", "preco": "29.90", "categoria": "cabos", "estoque": 14},
]


def buscar(termo: str = "") -> list[dict]:
    termo = termo.strip().lower()
    return [p for p in PRODUTOS if termo in p["nome"].lower()]


def por_slug(slug: str) -> dict | None:
    return next((p for p in PRODUTOS if p["slug"] == slug), None)
```
```python
import json

from django.http import Http404, HttpResponse, HttpResponseBadRequest, JsonResponse
from django.middleware.csrf import get_token
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.html import escape
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_http_methods

from . import dados


@require_GET
def lista(request):
    """GET /produtos/?busca=mouse  → HTML montado à mão (os templates da aula 03 resolvem isto)."""
    itens = dados.buscar(request.GET.get("busca", ""))
    linhas = "".join(
        f'<li><a href="{reverse("catalog:detail", kwargs={"slug": p["slug"]})}">{escape(p["nome"])}</a> — R$ {p["preco"]}</li>'
        for p in itens
    )
    return HttpResponse(f"<h1>Produtos ({len(itens)})</h1><ul>{linhas}</ul>")


@require_GET
def detalhe(request, slug):
    """GET /produtos/<slug>/ → 200 ou 404."""
    produto = dados.por_slug(slug)
    if produto is None:
        raise Http404(f"Produto '{slug}' não existe")
    return HttpResponse(f"<h1>{escape(produto['nome'])}</h1><p>R$ {produto['preco']} · estoque: {produto['estoque']}</p>")


@require_GET
def api_lista(request):
    """GET /api/produtos/?busca=… → JSON (o Módulo 6 faz isto direito com o DRF)."""
    itens = dados.buscar(request.GET.get("busca", ""))
    return JsonResponse({"total": len(itens), "itens": itens}, json_dumps_params={"ensure_ascii": False})


@require_http_methods(["GET", "POST"])
@ensure_csrf_cookie                          # garante o cookie csrftoken na resposta do GET
def contato(request):
    """GET devolve o token; POST (JSON ou formulário) recebe a mensagem. Sem token CSRF o POST leva 403."""
    if request.method == "GET":
        return JsonResponse({"csrf": get_token(request), "dica": "envie o token no cabeçalho X-CSRFToken"})
    try:
        dados_post = json.loads(request.body) if request.content_type == "application/json" else request.POST.dict()
    except json.JSONDecodeError:
        return HttpResponseBadRequest("JSON inválido")
    nome, mensagem = dados_post.get("nome", "").strip(), dados_post.get("mensagem", "").strip()
    if not nome or not mensagem:
        return JsonResponse({"erro": "nome e mensagem são obrigatórios"}, status=422)
    return JsonResponse({"recebido": {"nome": nome, "mensagem": mensagem}}, status=201)


def antiga(request):
    """Redirecionamento permanente: /loja/ → /produtos/ (301, aula 2.02)."""
    return redirect("catalog:list", permanent=True)
```
**2. As URLs do app e do projeto**
```python
from django.urls import path

from . import views

app_name = "catalog"                                   # namespace: catalog:list, catalog:detail

urlpatterns = [
    path("produtos/", views.lista, name="list"),
    path("produtos/<slug:slug>/", views.detalhe, name="detail"),
    path("api/produtos/", views.api_lista, name="api_list"),
    path("contato/", views.contato, name="contact"),
    path("loja/", views.antiga, name="old"),
]
```
```python
from django.db import connection
from django.http import JsonResponse


def saude(request):
    """Health check: usado por balanceadores, Docker e monitoramento (Módulo 14). Confere também o banco."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        banco = "ok"
    except Exception:
        banco = "falhou"
    status = 200 if banco == "ok" else 503
    return JsonResponse({"status": "ok" if status == 200 else "degradado", "banco": banco}, status=status)
```
```python
from django.contrib import admin
from django.urls import include, path

from . import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("saude/", views.saude, name="health"),
    path("", include("apps.catalog.urls")),            # as rotas do catálogo na raiz
]
```
**3. `reverse()` e `resolve()`: o nome vira URL, e a URL vira nome**
```python
import os
import django

os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"
django.setup()
from django.urls import resolve, reverse

print(reverse("catalog:list"))
print(reverse("catalog:detail", kwargs={"slug": "mouse-sem-fio"}))
r = resolve("/produtos/mouse-sem-fio/")
print(r.view_name, r.kwargs, r.func.__name__, r.namespace)
print(resolve("/api/produtos/").url_name)
try:
    reverse("catalog:detail", kwargs={"slug": "Com Espaço"})            # não casa com o converter slug
except Exception as e:
    print(type(e).__name__)
```
```bash
uv run python explorar_urls.py
```
```text
/produtos/
/produtos/mouse-sem-fio/
catalog:detail {'slug': 'mouse-sem-fio'} detalhe catalog
api_list
NoReverseMatch
```
**4. Rodando e conferindo cada resposta (servidor real + `curl`)**
```python
import subprocess, time, urllib.request
servidor = subprocess.Popen(["uv", "run", "python", "manage.py", "runserver", "8121", "--noreload"],
                            stdout=open("servidor.log", "w"), stderr=subprocess.STDOUT)
for _ in range(60):
    try:
        urllib.request.urlopen("http://127.0.0.1:8121/saude/", timeout=1); break
    except Exception:
        time.sleep(0.5)
print("servidor no ar")
```
```text
servidor no ar
```
```bash
B=http://127.0.0.1:8121
echo "# lista (HTML) com busca"; curl -s "$B/produtos/?busca=mouse"; echo
echo "# detalhe"; curl -s $B/produtos/monitor-27-4k/; echo
echo "# 404 (a página de erro de produção seria a do 404.html; aqui, DEBUG=True mostra a do desenvolvedor)"
curl -s -o /dev/null -w "%{http_code}\n" $B/produtos/nao-existe/
echo "# 301: sem a barra final (APPEND_SLASH) e rota antiga"; curl -s -i $B/produtos | grep -iE "^HTTP|^location"; curl -s -i $B/loja/ | grep -iE "^HTTP|^location"
echo "# JSON"; curl -s "$B/api/produtos/?busca=soundbar"; echo
echo "# health check"; curl -s $B/saude/; echo
```
```text
# lista (HTML) com busca
<h1>Produtos (1)</h1><ul><li><a href="/produtos/mouse-sem-fio/">Mouse sem fio</a> — R$ 89.90</li></ul>
# detalhe
<h1>Monitor 27&quot; 4K</h1><p>R$ 2199.00 · estoque: 5</p>
# 404 (a página de erro de produção seria a do 404.html; aqui, DEBUG=True mostra a do desenvolvedor)
404
# 301: sem a barra final (APPEND_SLASH) e rota antiga
HTTP/1.1 301 Moved Permanently
Location: /produtos/
HTTP/1.1 301 Moved Permanently
Location: /produtos/
# JSON
{"total": 1, "itens": [{"slug": "soundbar", "nome": "Soundbar", "preco": "449.90", "categoria": "audio", "estoque": 0}]}
# health check
{"status": "ok", "banco": "ok"}
```
**5. O CSRF na prática (o `403` e o jeito certo)**
```bash
B=http://127.0.0.1:8121
echo "# 1) POST SEM token CSRF → 403"
curl -s -o /dev/null -w "%{http_code}\n" -X POST -H "Content-Type: application/json" -d '{"nome":"Ana","mensagem":"Oi"}' $B/contato/
echo "# 2) GET para receber o cookie csrftoken"
rm -f jar.txt; curl -s -c jar.txt $B/contato/ | head -c 120; echo
TOKEN=$(awk '$6=="csrftoken"{print $7}' jar.txt)
echo "# 3) POST COM cookie + cabeçalho X-CSRFToken → 201"
curl -s -w " [%{http_code}]\n" -b jar.txt -X POST -H "X-CSRFToken: $TOKEN" -H "Content-Type: application/json" -d '{"nome":"Ana","mensagem":"Oi, tudo bem?"}' $B/contato/
echo "# 4) validação → 422 e JSON inválido → 400"
curl -s -w " [%{http_code}]\n" -b jar.txt -X POST -H "X-CSRFToken: $TOKEN" -H "Content-Type: application/json" -d '{"nome":""}' $B/contato/
curl -s -o /dev/null -w "[%{http_code}]\n" -b jar.txt -X POST -H "X-CSRFToken: $TOKEN" -H "Content-Type: application/json" -d '{ruim' $B/contato/
echo "# 5) método errado: SEM token o 403 do CSRF vem primeiro; COM token, a view responde 405 com Allow"
curl -s -o /dev/null -w "sem token: %{http_code}\n" -X POST $B/produtos/
curl -s -i -b jar.txt -X POST -H "X-CSRFToken: $TOKEN" $B/produtos/ | grep -iE "^HTTP|^allow"
```
```text
# 1) POST SEM token CSRF → 403
403
# 2) GET para receber o cookie csrftoken
{"csrf": "P14XwEvOsZ3hMxh81WAyTeIAMalC396YwafnXFI5YPIjQQ04NAfYz1vVSxhqHhU5", "dica": "envie o token no cabe\u00e7alho X-
# 3) POST COM cookie + cabeçalho X-CSRFToken → 201
{"recebido": {"nome": "Ana", "mensagem": "Oi, tudo bem?"}} [201]
# 4) validação → 422 e JSON inválido → 400
{"erro": "nome e mensagem s\u00e3o obrigat\u00f3rios"} [422]
[400]
# 5) método errado: SEM token o 403 do CSRF vem primeiro; COM token, a view responde 405 com Allow
sem token: 403
HTTP/1.1 405 Method Not Allowed
Allow: GET
```
Repare no passo 5: o `403` do CSRF acontece **antes** da view, porque o *middleware* (a “cebola” da aula 01) roda primeiro; só com um token válido o `@require_GET` chega a responder `405`. Por isso, em testes e em depuração, a **ordem das camadas** explica respostas que parecem “erradas”.

O mecanismo: o cookie `csrftoken` vem no `GET`; o `POST` precisa devolver o **mesmo segredo** no cabeçalho (ou no campo oculto `csrfmiddlewaretoken` de um formulário). Um site malicioso consegue **disparar** o `POST` (o navegador anexa o cookie), mas **não consegue ler** o token para pô-lo no cabeçalho (política de mesma origem, aula 4.06).
```python
servidor.terminate(); servidor.wait()
print("servidor encerrado; linhas do log:", len(open("servidor.log").read().splitlines()))
```
```text
servidor encerrado; linhas do log: 22
```
**6. Testes das views (cliente de testes + pytest)**
```python
import pytest
from django.test import Client
from django.urls import reverse

pytestmark = pytest.mark.django_db        # o MetricasMiddleware abre conexão (aula 01)


def test_lista_sem_filtro_mostra_todos(client):
    resposta = client.get(reverse("catalog:list"))
    assert resposta.status_code == 200
    assert "Produtos (6)" in resposta.content.decode()


def test_busca_filtra_e_escapa_html(client):
    corpo = client.get(reverse("catalog:list"), {"busca": "monitor"}).content.decode()
    assert "Produtos (1)" in corpo and "Monitor 27&quot; 4K" in corpo        # as aspas do nome foram ESCAPADAS


def test_detalhe_existente_e_inexistente(client):
    assert client.get(reverse("catalog:detail", kwargs={"slug": "soundbar"})).status_code == 200
    assert client.get(reverse("catalog:detail", kwargs={"slug": "nao-existe"})).status_code == 404


def test_metodo_nao_permitido_devolve_405_com_allow(client):
    resposta = client.post(reverse("catalog:list"))
    assert resposta.status_code == 405 and "GET" in resposta["Allow"]


def test_api_devolve_json(client):
    dados = client.get(reverse("catalog:api_list"), {"busca": "fone"}).json()
    assert dados["total"] == 1 and dados["itens"][0]["slug"] == "fone-bluetooth"


def test_redirecionamento_permanente(client):
    resposta = client.get("/loja/")
    assert resposta.status_code == 301 and resposta["Location"] == reverse("catalog:list")


def test_post_sem_csrf_e_rejeitado_com_checagem_ligada():
    c = Client(enforce_csrf_checks=True)       # o cliente de testes normalmente PULA o CSRF; aqui ligamos de propósito
    assert c.post(reverse("catalog:contact"), {"nome": "A", "mensagem": "B"}).status_code == 403


def test_post_valido_e_invalido(client):
    ok = client.post(reverse("catalog:contact"), {"nome": "Ana", "mensagem": "Oi"})
    assert ok.status_code == 201 and ok.json()["recebido"]["nome"] == "Ana"
    assert client.post(reverse("catalog:contact"), {"nome": ""}).status_code == 422
    assert client.post(reverse("catalog:contact"), "{ruim", content_type="application/json").status_code == 400


def test_health_check(client):
    resposta = client.get(reverse("health"))
    assert resposta.status_code == 200 and resposta.json() == {"status": "ok", "banco": "ok"}
```
```bash
touch apps/catalog/tests/__init__.py
rm -f apps/catalog/tests.py
uv run pytest
```
```text
.............                                                            [100%]
13 passed in 0.26s
```
(O `startapp` criou um `tests.py` que conflitaria com a pasta `tests/`: removemos.)

## ⚠️ Erros comuns e boas práticas
| Mensagem / sintoma | Causa | Solução |
|---|---|---|
| `Page not found (404)` com a lista “Django tried these URL patterns” | Rota inexistente ou ordem errada (DEBUG mostra as tentativas) | Confira `urlpatterns` e a barra final |
| `NoReverseMatch: Reverse for 'detail' not found` | Nome/`app_name` errado ou argumentos que não casam com o *converter* | `reverse("catalog:detail", kwargs={"slug": ...})` com valor válido |
| `TypeError: lista() got an unexpected keyword argument 'slug'` | A rota captura `<slug>` mas a view não aceita o parâmetro | A assinatura da *view* deve ter o mesmo nome |
| `ValueError: The view ... didn't return an HttpResponse object. It returned None instead.` | Esqueceu o `return` | Toda *view* devolve uma resposta |
| `Forbidden (403) CSRF verification failed. Request aborted.` | `POST` sem token | `{% csrf_token %}` no formulário ou `X-CSRFToken` no *fetch*; `@csrf_exempt` só com outra autenticação |
| `405 Method Not Allowed` | Decorator restringe o método | Envie o método correto (veja `Allow`) |
| `UnicodeDecodeError`/acentos quebrados em `JsonResponse` | `ensure_ascii` | Funciona, mas pode-se usar `json_dumps_params={"ensure_ascii": False}` |
| Links quebram ao mudar uma rota | URLs escritas à mão | Sempre `reverse()` / `{% url %}` |
| `RuntimeError: You called this URL via POST, but the URL doesn't end in a slash and you have APPEND_SLASH set.` | `POST` para URL sem barra final | Use a URL com `/` |
| Teste “passa” sem CSRF | O `Client` do Django não o aplica por padrão | `Client(enforce_csrf_checks=True)` para testar |

- **Nunca** monte HTML com texto de usuário sem escapar (`escape`/*templates*): os *templates* da aula 03 fazem isso automaticamente (*autoescape*).
- Use o **status HTTP certo** (200, 201, 301, 400, 403, 404, 405, 422); a API (Módulo 6) depende disso.
- Mantenha as *views* **finas**: validação e regra de negócio vão para formulários, *services* e modelos (Módulo 8).
- Dê nome a **todas** as rotas e use *namespaces* de app.
- `@csrf_exempt` não é solução para “o formulário não funciona”: é uma decisão de segurança.

## 🧠 Pausa para lógica
**Problema (um roteador com *converters* e `reverse`).** Reimplemente em Python puro uma versão mínima do `path()`: `compilar("produtos/<slug:slug>/")` devolve um objeto com `resolver(caminho)` (devolve os argumentos ou `None`) e `reverso(**kwargs)` (monta o caminho, validando contra o *converter*). Compare com o `resolve`/`reverse` do Django.

<details><summary>Dica</summary>
Troque cada <code>&lt;tipo:nome&gt;</code> por um grupo regex nomeado com o padrão do <em>converter</em> (<code>int → [0-9]+</code>, <code>slug → [-a-zA-Z0-9_]+</code>, <code>str → [^/]+</code>) e converta o valor capturado (<code>int(...)</code>). O <code>reverso</code> valida cada argumento com o mesmo padrão antes de montar o caminho.
</details>

<details><summary>Solução comentada</summary>

```python
import re

CONVERTERS = {
    "str":  (r"[^/]+", str),
    "int":  (r"[0-9]+", int),
    "slug": (r"[-a-zA-Z0-9_]+", str),
}


PARAM = re.compile(r"<(?:(\w+):)?(\w+)>")                 # <tipo:nome> ou <nome>


class Rota:
    def __init__(self, padrao: str):
        self.padrao, self.tipos = padrao, {}
        regex = ""
        for pedaco in re.split(r"(<(?:\w+:)?\w+>)", padrao):          # alterna texto fixo e parâmetros
            m = PARAM.fullmatch(pedaco)
            if m:
                tipo, nome = m.group(1) or "str", m.group(2)
                self.tipos[nome] = tipo
                regex += f"(?P<{nome}>{CONVERTERS[tipo][0]})"
            else:
                regex += re.escape(pedaco)
        self.regex = re.compile(f"^{regex}$")

    def resolver(self, caminho: str):
        m = self.regex.match(caminho)
        return None if not m else {n: CONVERTERS[self.tipos[n]][1](v) for n, v in m.groupdict().items()}

    def reverso(self, **kwargs):
        def trocar(m):
            tipo, nome = m.group(1) or "str", m.group(2)
            valor = str(kwargs[nome])
            if not re.fullmatch(CONVERTERS[tipo][0], valor):
                raise ValueError(f"'{valor}' não casa com o converter {tipo}")
            return valor
        return PARAM.sub(trocar, self.padrao)


rota = Rota("produtos/<slug:slug>/")
print(rota.resolver("produtos/mouse-sem-fio/"), rota.resolver("produtos/Com Espaço/"), rota.resolver("produtos/a/b/"))
print(rota.reverso(slug="mouse-sem-fio"))
item = Rota("pedidos/<int:pk>/itens/<int:n>/")
print(item.resolver("pedidos/42/itens/3/"), item.resolver("pedidos/abc/itens/3/"), item.reverso(pk=7, n=1))
try:
    item.reverso(pk="x", n=1)
except ValueError as e:
    print("erro:", e)
```
```bash
uv run python mini_path.py
```
```text
{'slug': 'mouse-sem-fio'} None None
produtos/mouse-sem-fio/
{'pk': 42, 'n': 3} None pedidos/7/itens/1/
erro: 'x' não casa com o converter int
```
É o essencial do `path()`: **padrão → regex** para casar (e converter os tipos), **o mesmo padrão ao contrário** para gerar a URL. O Django acrescenta compilação em cache, *namespaces*, `re_path`, converters personalizados e mensagens de erro.
</details>

**Variação mais difícil:** suporte a um *converter* `uuid` e a rotas com parâmetro opcional; e escreva um teste que garanta que `reverso(resolver(x)) == x` para 100 caminhos gerados.

## 🧩 Exercícios
**1. Fixação**
(a) Por que usar `reverse()` em vez de escrever `"/produtos/"`? (b) O que acontece se duas rotas casam com o mesmo caminho? (c) Que status o Django devolve para `POST /produtos/` em uma view `@require_GET`? (d) Por que o `Client` de testes não acusa o CSRF por padrão?

<details><summary>Solução</summary>

(a) A URL passa a ter **um só ponto de definição**: mudar a rota não quebra links nem redirecionamentos. (b) A primeira da lista vence; por isso rotas específicas vêm antes das genéricas. (c) `405 Method Not Allowed` com o cabeçalho `Allow: GET`. (d) Para simplificar testes; use `Client(enforce_csrf_checks=True)` quando quiser testar a proteção.
</details>

**2. Aplicação no projeto MiniShop**
Evolua o catálogo com as rotas definitivas e testes.

Critérios de pronto:
- [ ] Rotas `produtos/`, `produtos/<slug:slug>/`, `api/produtos/`, `contato/`, `saude/` com `name` e `app_name`; **nenhuma URL escrita à mão** no código (só `reverse`)
- [ ] A rota `categorias/<slug:categoria>/` lista só os produtos daquela categoria (filtrando a lista provisória) e devolve `404` se a categoria não existir
- [ ] Todas as *views* só aceitam os métodos que fazem sentido (405 nos demais)
- [ ] `/saude/` devolve `200` com o estado do banco e `503` quando o banco falha (teste isso simulando a falha com `unittest.mock.patch`)
- [ ] ≥ 12 testes passando (`uv run pytest`), incluindo `404`, `405`, `301`, CSRF e validação (`422`/`400`)
- [ ] `docs/rotas.md` com a tabela de rotas (método, URL, nome, *view*, status possíveis)
- [ ] Commit `feat(catalog): url routes and function views`

<details><summary>Solução de referência</summary>

```python
# em apps/catalog/views.py
@require_GET
def por_categoria(request, categoria):
    itens = [p for p in dados.PRODUTOS if p["categoria"] == categoria]
    if not itens:
        raise Http404("categoria inexistente")
    return JsonResponse({"categoria": categoria, "itens": itens}, json_dumps_params={"ensure_ascii": False})
# em urls.py: path("categorias/<slug:categoria>/", views.por_categoria, name="category")
# teste do 503:
from unittest.mock import patch
def test_saude_degradada(client):
    with patch("config.views.connection.cursor", side_effect=Exception("sem banco")):
        r = client.get(reverse("health"))
    assert r.status_code == 503 and r.json()["banco"] == "falhou"
```
</details>

**3. Desafio (opcional)**
Crie um *converter* próprio `<sku:codigo>` (classe com `regex`, `to_python`, `to_url`, registrada com `register_converter`) que aceite códigos como `MN-04` e devolva em maiúsculas.

## 🎤 Na entrevista
- **Como o Django escolhe qual view atende uma URL?** Percorre `urlpatterns` do `ROOT_URLCONF` em ordem e usa a primeira rota que casa; `include` delega prefixos a outros módulos; os *converters* capturam parâmetros.
- **Para que servem `name` e `reverse()`?** Dar nomes às rotas e gerar URLs a partir deles, evitando URLs fixas no código e nos templates.
- **O que é CSRF e como o Django o previne?** Ataque em que outro site faz o navegador logado enviar uma requisição que altera dados; o Django exige um token secreto (cookie + campo/cabeçalho) em métodos não seguros, e responde `403` se faltar.
- **Qual a diferença entre `HttpResponse`, `JsonResponse` e `redirect`?** Resposta genérica (texto/HTML, status e cabeçalhos livres), resposta com corpo JSON e `Content-Type: application/json`, e resposta `301/302` com `Location`.
- **Como você restringe os métodos HTTP de uma view?** Com `@require_http_methods([...])` (ou `require_GET`/`require_POST`), que devolve `405` com o cabeçalho `Allow`.

## 📚 Para ir além
- 📄 Documentação oficial: [Despachante de URLs](https://docs.djangoproject.com/en/5.2/topics/http/urls/). `path`, converters, `include`, `reverse`, namespaces.
- 📄 Documentação oficial: [Escrevendo views](https://docs.djangoproject.com/en/5.2/topics/http/views/) e [Objetos de requisição e resposta](https://docs.djangoproject.com/en/5.2/ref/request-response/). Tudo sobre `HttpRequest`/`HttpResponse`.
- 📄 Documentação oficial: [Proteção contra CSRF](https://docs.djangoproject.com/en/5.2/ref/csrf/). Como funciona e como usar com AJAX/*fetch*.
- 📄 Documentação oficial: [Testes no Django](https://docs.djangoproject.com/en/5.2/topics/testing/overview/). Cliente de testes, `Client(enforce_csrf_checks=True)`.
- 🏋️ Prática extra: escreva uma view `GET /produtos/exportar.csv` que devolve um CSV com `Content-Disposition: attachment` (use `HttpResponse` e o módulo `csv`).

## ✅ Checklist da aula
- [ ] Rotas com `name` e `app_name`, e links gerados só com `reverse()`
- [ ] Views de função com status HTTP corretos (200, 201, 301, 400, 403, 404, 405, 422)
- [ ] Reproduzi o `403` do CSRF e o corrigi com o token
- [ ] Testes do catálogo passando
- [ ] Fiz o commit do exercício
