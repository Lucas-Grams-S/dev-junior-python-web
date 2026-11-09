# 02. HTTP: métodos, status codes, headers e corpo

> ⏱️ ~1h30 · Módulo 2 · Pré-requisitos: [01](01-cliente-servidor-dns-tcp.md)

## 🎯 Objetivos
Ao final desta aula você consegue:
- Ler e escrever à mão uma requisição e uma resposta HTTP/1.1
- Escolher o método correto (`GET`, `POST`, `PUT`, `PATCH`, `DELETE`) e dizer se é seguro e idempotente
- Interpretar as famílias de status code e os mais usados (200, 201, 204, 301/302, 400, 401, 403, 404, 409, 422, 500)
- Usar os headers `Content-Type`, `Content-Length`, `Accept`, `Authorization`, `Location` e `Cache-Control`
- Explicar que HTTP é *stateless*

## 🤔 Por que isso importa
Toda API, todo site e todo webhook falam HTTP. Quando uma integração falha, você precisa olhar a requisição bruta: método, URL, headers, corpo e o status da resposta. Dominar isso é a base de REST (Módulo 6) e de depurar qualquer problema web.

## 💡 Intuição (explicação simples)
HTTP é um **balcão de atendimento**: você chega com um **pedido** (o que quer, onde e com quais documentos), o atendente devolve uma **resposta** (o resultado e um código dizendo como foi) e o balcão **esquece você**: o próximo atendimento começa do zero (*stateless*). Se o atendente precisa lembrar de você (carrinho, login), você traz uma **senha/ficha** a cada visita (cookie ou token, aula 03).

## 🔬 Como funciona por dentro
Sobre a conexão TCP (aula 01), o cliente envia texto estruturado:

```text
GET /produtos?busca=mouse HTTP/1.1        ← linha de requisição: método, alvo, versão
Host: localhost:8765                       ← headers (um por linha: Nome: valor)
Accept: application/json
                                           ← linha em branco encerra os headers
(corpo opcional)
```
e o servidor responde:
```text
HTTP/1.1 200 OK                            ← versão, status, texto
Content-Type: application/json; charset=utf-8
Content-Length: 42

{"produtos": [...]}                        ← corpo
```
- `\r\n` (CRLF) termina cada linha; a linha em branco separa headers e corpo.
- O tamanho do corpo é dado por `Content-Length` (ou *chunked*): é assim que o HTTP resolve o problema das fronteiras do TCP.
- HTTP/1.1 reaproveita a conexão (*keep-alive*); HTTP/2 multiplexa vários pedidos em uma conexão; HTTP/3 usa QUIC (sobre UDP). A semântica (métodos, status, headers) é a mesma.

**Métodos**

| Método | Uso | Seguro* | Idempotente** | Tem corpo |
|---|---|---|---|---|
| `GET` | ler um recurso | sim | sim | não |
| `HEAD` | só os headers do GET | sim | sim | não |
| `POST` | criar / executar ação | não | **não** | sim |
| `PUT` | substituir inteiro | não | sim | sim |
| `PATCH` | alterar parcialmente | não | em geral não | sim |
| `DELETE` | remover | não | sim | raro |
| `OPTIONS` | o que é permitido (CORS) | sim | sim | não |

\* *seguro* = não altera estado no servidor. \*\* *idempotente* = repetir N vezes tem o mesmo efeito que 1 vez (crítico em retentativas e pagamentos: Módulo 7).

**Status codes**

| Faixa | Significado | Mais usados |
|---|---|---|
| 1xx | informativo | 101 (WebSocket) |
| 2xx | sucesso | 200 OK · 201 Created · 204 No Content |
| 3xx | redirecionamento | 301 permanente · 302/307 temporário · 304 Not Modified |
| 4xx | **erro do cliente** | 400 Bad Request · 401 não autenticado · 403 proibido · 404 não existe · 405 método não permitido · 409 conflito · 422 dados inválidos · 429 muitas requisições |
| 5xx | **erro do servidor** | 500 erro interno · 502/503/504 (proxy/indisponível/timeout) |

Regra mnemônica: **401 = “quem é você?”**, **403 = “sei quem é, mas não pode”**.

**Headers úteis:** `Host`, `Content-Type` (formato do corpo enviado), `Accept` (formato desejado), `Authorization` (credenciais), `Location` (para onde ir, em 201/3xx), `Cache-Control`, `User-Agent`, `Set-Cookie`/`Cookie` (aula 03).

## 🛠️ Exemplo prático
Subimos um servidor HTTP mínimo (biblioteca padrão) e falamos com ele **por socket puro**, para ver o texto bruto.

**1. O servidor de teste**
```python
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

PRODUTOS = [{"sku": "MS-01", "nome": "Mouse", "preco": "49.90"}]

class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    def log_message(self, *a): pass                 # silencia o log

    def _responder(self, status, corpo=None, extra=None):
        dados = json.dumps(corpo).encode() if corpo is not None else b""
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(dados)))
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(dados)

    def do_GET(self):
        if self.path == "/produtos":
            self._responder(200, PRODUTOS)
        else:
            self._responder(404, {"erro": "não encontrado"})

    def do_POST(self):
        tamanho = int(self.headers.get("Content-Length", 0))
        try:
            novo = json.loads(self.rfile.read(tamanho))
        except json.JSONDecodeError:
            return self._responder(400, {"erro": "JSON inválido"})
        PRODUTOS.append(novo)
        self._responder(201, novo, {"Location": f"/produtos/{novo['sku']}"})

srv = HTTPServer(("127.0.0.1", 8765), Handler)
threading.Thread(target=srv.serve_forever, daemon=True).start()
print("servidor no ar em http://127.0.0.1:8765")
```
```text
servidor no ar em http://127.0.0.1:8765
```

**2. Uma requisição escrita à mão (socket puro)**
```python
import socket

def requisicao(texto: str) -> str:
    with socket.create_connection(("127.0.0.1", 8765), timeout=2) as s:
        s.sendall(texto.replace("\n", "\r\n").encode())
        s.settimeout(0.5)
        partes = []
        try:
            while chunk := s.recv(4096):
                partes.append(chunk)
        except TimeoutError:
            pass
    return b"".join(partes).decode()

resp = requisicao("GET /produtos HTTP/1.1\nHost: localhost\nConnection: close\n\n")
print(resp)
```
```text
HTTP/1.1 200 OK
Server: BaseHTTP/0.6 Python/3.13.18
Date: Sun, 08 Nov 2026 00:39:36 GMT
Content-Type: application/json; charset=utf-8
Content-Length: 53

[{"sku": "MS-01", "nome": "Mouse", "preco": "49.90"}]
```
Observe a linha de status, os headers, a linha em branco e o corpo JSON.

**3. Criando com POST (201 + `Location`) e erros 400/404**
```python
import json

corpo = json.dumps({"sku": "TC-02", "nome": "Teclado", "preco": "120.00"})
post = (f"POST /produtos HTTP/1.1\nHost: localhost\nContent-Type: application/json\n"
        f"Content-Length: {len(corpo.encode())}\nConnection: close\n\n{corpo}")
print(requisicao(post).split("\r\n\r\n")[0])
print("---")
print(requisicao("GET /nada HTTP/1.1\nHost: localhost\nConnection: close\n\n").splitlines()[0])
ruim = "{quebrado"
print(requisicao(f"POST /produtos HTTP/1.1\nHost: localhost\nContent-Length: {len(ruim)}\nConnection: close\n\n{ruim}").splitlines()[0])
```
```text
HTTP/1.1 201 Created
Server: BaseHTTP/0.6 Python/3.13.18
Date: Sun, 08 Nov 2026 00:39:36 GMT
Content-Type: application/json; charset=utf-8
Content-Length: 54
Location: /produtos/TC-02
---
HTTP/1.1 404 Not Found
HTTP/1.1 400 Bad Request
```

**4. O mesmo com a biblioteca padrão (`http.client`) e `urllib`**
```python
import http.client
import json
import urllib.request

c = http.client.HTTPConnection("127.0.0.1", 8765)
c.request("GET", "/produtos", headers={"Accept": "application/json"})
r = c.getresponse()
print(r.status, r.reason, r.getheader("Content-Type"))
print([p["sku"] for p in json.loads(r.read())])
c.close()

with urllib.request.urlopen("http://127.0.0.1:8765/produtos") as r2:
    print(r2.status, len(json.load(r2)))
```
```text
200 OK application/json; charset=utf-8
['MS-01', 'TC-02']
200 2
```

**5. Sem estado (stateless): cada requisição é independente**
```python
for _ in range(2):
    print(requisicao("GET /produtos HTTP/1.1\nHost: localhost\nConnection: close\n\n").splitlines()[0])
```
```text
HTTP/1.1 200 OK
HTTP/1.1 200 OK
```
O servidor não “lembra” que você já pediu antes; qualquer memória precisa vir na própria requisição (cookie, token) ou ficar em um banco.

## ⚠️ Erros comuns e boas práticas
| Sintoma | Causa | Solução |
|---|---|---|
| `400 Bad Request` | JSON malformado, header faltando, corpo inconsistente com `Content-Length` | Valide o JSON; confira `Content-Type` |
| `405 Method Not Allowed` | Método que a rota não aceita | Confira o `Allow` na resposta |
| `415 Unsupported Media Type` | `Content-Type` incorreto | `Content-Type: application/json` |
| `401` vs `403` confundidos | Falta de credencial vs falta de permissão | 401 = autentique-se; 403 = sem autorização |
| API devolve `200` com `{"erro": ...}` | Status code ignorado | Use o código correto; o cliente decide por ele |
| Retentativa cobra duas vezes | `POST` não é idempotente | Chave de idempotência (Módulo 7) |

- Use o **status code certo**: monitoramento, cache e clientes dependem dele.
- `GET` nunca altera dados (um rastreador ou *prefetch* pode chamá-lo).
- Nunca coloque senha/token na URL (vai para logs e histórico); use `Authorization`.
- `Content-Type` descreve o que **você envia**; `Accept` descreve o que **quer receber**.

## 🧠 Pausa para lógica
**Problema (parser).** Dado o texto bruto de uma requisição HTTP, devolva `(método, caminho, headers, corpo)`. Headers são case-insensitive e o corpo tem o tamanho de `Content-Length`.

<details><summary>Dica</summary>
Separe cabeçalho e corpo no primeiro <code>\r\n\r\n</code>; a 1ª linha tem 3 partes; cada header se divide no primeiro <code>:</code> (<code>split(":", 1)</code>). Guarde as chaves em minúsculas.
</details>

<details><summary>Solução comentada</summary>

```python
def parsear(bruto: str):
    cabecalho, _, corpo = bruto.partition("\r\n\r\n")
    linhas = cabecalho.split("\r\n")
    metodo, caminho, versao = linhas[0].split(" ", 2)
    headers = {}
    for linha in linhas[1:]:
        nome, _, valor = linha.partition(":")
        headers[nome.strip().lower()] = valor.strip()
    tamanho = int(headers.get("content-length", 0))
    return metodo, caminho, headers, corpo[:tamanho]

bruto = "POST /produtos HTTP/1.1\r\nHost: x\r\nContent-Type: application/json\r\nContent-Length: 14\r\n\r\n{\"sku\": \"A-1\"}EXTRA"
print(parsear(bruto))
```
```text
('POST', '/produtos', {'host': 'x', 'content-type': 'application/json', 'content-length': '14'}, '{"sku": "A-1"}')
```
O `EXTRA` é descartado porque o `Content-Length` manda. É o que todo servidor faz antes de entregar a requisição ao seu código.
</details>

**Variação mais difícil:** trate headers repetidos (`Set-Cookie` pode aparecer várias vezes) e o caso de corpo menor que o `Content-Length` (requisição incompleta: o servidor deve esperar mais bytes).

## 🧩 Exercícios
**1. Fixação**
Que status você devolveria para: (a) criar um produto com sucesso; (b) listar sem estar logado; (c) SKU já existente; (d) usuário comum tentando apagar um produto; (e) erro inesperado no banco?

<details><summary>Solução</summary>

(a) 201 (com `Location`). (b) 401. (c) 409 (ou 422, conforme o contrato). (d) 403. (e) 500 (sem vazar detalhes internos).
</details>

**2. Aplicação no projeto MiniShop**
Escreva à mão (em `docs/http-exemplos.md`) as requisições e respostas esperadas da futura API: listar produtos, obter um, criar, atualizar preço, remover e um erro de validação.

Critérios de pronto:
- [ ] Cada exemplo tem linha de requisição, headers relevantes, corpo e a resposta completa com o status certo
- [ ] `POST` devolve `201` + `Location`; `DELETE` devolve `204`
- [ ] Erros têm corpo JSON com uma estrutura única (`{"erro": "...", "detalhes": ...}`)
- [ ] Indica, por rota, se é segura e idempotente
- [ ] Commit `docs: draft the minishop http contract`

<details><summary>Solução de referência</summary>

```text
GET /produtos/MS-01 HTTP/1.1
Accept: application/json
→ 200 OK  {"sku":"MS-01","nome":"Mouse","preco":"49.90","qtd":7}

POST /produtos HTTP/1.1                         (não idempotente)
Content-Type: application/json
{"sku":"MS-01","nome":"Mouse","preco":"49.90"}
→ 409 Conflict  {"erro":"SKU já existe"}

PATCH /produtos/MS-01  {"preco":"59.90"}       → 200 OK
DELETE /produtos/MS-01                          → 204 No Content (idempotente)
POST /produtos  {"sku":"","preco":"-1"}         → 422  {"erro":"dados inválidos","detalhes":{"sku":"obrigatório","preco":"negativo"}}
```
</details>

**3. Desafio (opcional)**
Faça o servidor da aula responder `405` com o header `Allow: GET, POST` quando alguém usar `DELETE /produtos`.

## 🎤 Na entrevista
- **O que significa HTTP ser *stateless*?** Cada requisição é independente; o servidor não guarda memória entre elas. Estado (login, carrinho) vem em cookies/tokens ou fica no servidor/banco, referenciado por um identificador.
- **Diferença entre `PUT` e `PATCH`? E entre `PUT` e `POST`?** `PUT` substitui o recurso inteiro (idempotente); `PATCH` altera partes; `POST` cria/executa ação e não é idempotente.
- **401 vs 403?** 401: não autenticado (faltam/estão inválidas as credenciais); 403: autenticado, porém sem permissão.

## 📚 Para ir além
- 📄 Documentação oficial: [HTTP (MDN)](https://developer.mozilla.org/pt-BR/docs/Web/HTTP). Guia completo em PT-BR.
- 📄 Documentação oficial: [Métodos de requisição HTTP (MDN)](https://developer.mozilla.org/pt-BR/docs/Web/HTTP/Reference/Methods). Segurança e idempotência de cada método.
- 📄 Documentação oficial: [Códigos de status HTTP (MDN)](https://developer.mozilla.org/pt-BR/docs/Web/HTTP/Reference/Status). Lista completa.
- 📄 Documentação oficial: [`http.server`](https://docs.python.org/3/library/http.server.html) e [`http.client`](https://docs.python.org/3/library/http.client.html). Servidor e cliente da biblioteca padrão.
- 🏋️ Prática extra: implemente `HEAD /produtos` no servidor (mesmos headers do GET, sem corpo).

## ✅ Checklist da aula
- [ ] Escrevi uma requisição HTTP à mão via socket
- [ ] Sei dizer segurança e idempotência de cada método
- [ ] Sei escolher o status code para cada situação
- [ ] Fiz o commit do exercício
