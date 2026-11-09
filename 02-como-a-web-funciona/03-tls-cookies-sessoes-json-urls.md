# 03. HTTPS/TLS, cookies, sessões, JSON, URLs e query strings

> ⏱️ ~1h30 · Módulo 2 · Pré-requisitos: [02](02-http-metodos-status-headers.md)

## 🎯 Objetivos
Ao final desta aula você consegue:
- Explicar o que o TLS garante (confidencialidade, integridade, autenticidade) e o papel dos certificados
- Montar e decompor URLs (esquema, host, porta, caminho, query, fragmento) e codificar caracteres especiais
- Usar JSON como formato de troca e saber seu mapa de tipos
- Explicar cookies, seus atributos de segurança (`HttpOnly`, `Secure`, `SameSite`) e como funciona uma sessão
- Comparar sessão no servidor com token enviado pelo cliente

## 🤔 Por que isso importa
Todo login, carrinho e “lembrar de mim” depende de cookies/sessões. Erros de configuração aqui viram vulnerabilidades (roubo de sessão, CSRF: Módulo 9). E toda API troca JSON por URLs com query strings. Você usará isso no primeiro dia de trabalho.

## 💡 Intuição (explicação simples)
- **HTTPS** = **carta lacrada entregue por um carteiro que verificou o RG do destinatário**: ninguém no caminho lê (cifra) nem altera (integridade), e você sabe que está falando com o site certo (certificado).
- **Cookie** = **pulseira de balada**: o servidor te entrega na entrada e, em cada visita, você mostra a pulseira; o balcão (sem memória) reconhece você por ela.
- **Sessão** = **ficha no arquivo do estabelecimento**: a pulseira só tem um número; os dados (quem é, o carrinho) ficam guardados no servidor, ligados a esse número.
- **URL** = **endereço completo com instruções**: rua (host), apartamento (porta), sala (caminho), observações (query).

## 🔬 Como funciona por dentro
**TLS (a base do HTTPS).** Após o TCP, cliente e servidor fazem um *handshake* TLS:
```mermaid
sequenceDiagram
    participant C as Navegador
    participant S as Servidor
    C->>S: ClientHello (versões e cifras que suporto)
    S-->>C: ServerHello + certificado (chave pública, assinado por uma CA)
    Note over C: valida: assinatura da CA, nome do domínio, validade
    C->>S: troca de chaves (ECDHE)
    Note over C,S: ambos derivam a mesma chave de sessão
    C->>S: dados HTTP cifrados com a chave de sessão
```
- **Criptografia assimétrica** só estabelece a chave; os dados trafegam com **criptografia simétrica** (rápida).
- O certificado liga um domínio a uma chave pública e é assinado por uma **autoridade certificadora (CA)** em que o seu sistema confia. Sem validação, qualquer um poderia se passar pelo banco.
- HTTPS = HTTP dentro de TLS (porta 443). TLS 1.2 e 1.3 são os usados hoje; versões antigas (SSL, TLS 1.0/1.1) são inseguras.

**URL.** `https://ana:senha@loja.com.br:8443/produtos/42?busca=mouse&pagina=2#avaliacoes`
`esquema` · `usuário:senha` (evite) · `host` · `porta` · `caminho` · `?query` · `#fragmento` (o fragmento **não** vai ao servidor). Caracteres especiais são *percent-encoded*: espaço → `%20`, `ã` → `%C3%A3` (UTF-8), `&` → `%26`.

**JSON ↔ Python:** objeto↔`dict`, array↔`list`, string↔`str`, número↔`int/float`, `true/false`↔`True/False`, `null`↔`None`. Não existem datas nem `Decimal`: viram texto (ISO 8601 `"2026-11-07T10:30:00Z"`; dinheiro como string).

**Cookies.** O servidor envia `Set-Cookie: nome=valor; atributos`; o navegador devolve `Cookie: nome=valor` em toda requisição ao mesmo site.

| Atributo | Efeito |
|---|---|
| `HttpOnly` | JavaScript **não** lê o cookie (mitiga roubo por XSS) |
| `Secure` | só enviado por HTTPS |
| `SameSite=Lax/Strict` | limita envio em requisições vindas de outros sites (mitiga CSRF) |
| `Max-Age` / `Expires` | validade (sem isso, cookie de sessão do navegador) |
| `Path` / `Domain` | onde vale |

**Sessão no servidor.** Login válido → servidor cria um ID aleatório, grava `{id: dados}` em memória/banco/Redis e manda `Set-Cookie: sessionid=ID`. Nas próximas requisições, lê o ID e recupera os dados. **Token (ex.: JWT)**: o próprio cliente guarda um token assinado com os dados e o envia em `Authorization: Bearer ...`; o servidor só valida a assinatura (comparação completa no Módulo 9).

| | Sessão (cookie) | Token no cabeçalho |
|---|---|---|
| Estado | no servidor | no cliente (assinado) |
| Revogar | fácil (apaga a sessão) | difícil (precisa de lista/expiração curta) |
| Ideal para | sites com HTML (Django) | APIs, apps móveis |

## 🛠️ Exemplo prático
**1. O TLS de verdade (precisa de internet; os valores variam com o tempo)**
```bash
curl -sv https://example.com -o /dev/null 2>&1 | grep -E "SSL connection|subject:|issuer:|expire date|HTTP/"
```
```text
* SSL connection using TLSv1.3 / TLS_AES_256_GCM_SHA384 / X25519MLKEM768 / id-ecPublicKey
*   subject: CN=example.com
*   expire date: Dec 25 22:56:35 2026 GMT
*   issuer: C=US; O=SSL Corporation; CN=Cloudflare TLS Issuing ECC CA 3
* using HTTP/2
* [HTTP/2] [1] OPENED stream for https://example.com/
* [HTTP/2] [1] [:method: GET]
* [HTTP/2] [1] [:scheme: https]
* [HTTP/2] [1] [:authority: example.com]
* [HTTP/2] [1] [:path: /]
* [HTTP/2] [1] [user-agent: curl/8.18.0]
* [HTTP/2] [1] [accept: */*]
> GET / HTTP/2
< HTTP/2 200
```
Você verá a versão do TLS, a cifra negociada, o dono do certificado (`subject`), quem o assinou (`issuer`) e a validade.

**2. Decompondo e montando URLs**
```python
from urllib.parse import parse_qs, quote, unquote, urlencode, urlparse, urljoin

u = urlparse("https://loja.com.br:8443/produtos/42?busca=mouse+gamer&pagina=2&cor=azul&cor=preto#avaliacoes")
print(u.scheme, u.hostname, u.port, u.path, u.fragment)
print(parse_qs(u.query))                      # valores são listas (a chave pode repetir)

print(urlencode({"busca": "teclado mecânico", "preco_max": "100&200"}))
print(quote("café com leite/açúcar"), quote("a/b", safe=""), unquote("caf%C3%A9"))
print(urljoin("https://loja.com.br/produtos/", "../carrinho"))
```
```text
https loja.com.br 8443 /produtos/42 avaliacoes
{'busca': ['mouse gamer'], 'pagina': ['2'], 'cor': ['azul', 'preto']}
busca=teclado+mec%C3%A2nico&preco_max=100%26200
caf%C3%A9%20com%20leite/a%C3%A7%C3%BAcar a%2Fb café
https://loja.com.br/carrinho
```
Nunca monte URLs com `+` de strings: `urlencode` evita bugs com `&`, `=` e acentos.

**3. JSON na prática**
```python
import json
from decimal import Decimal
from datetime import datetime, timezone

pedido = {"id": 10, "pago": False, "desconto": None, "itens": [{"sku": "MS-01", "qtd": 2}],
          "total": str(Decimal("99.80")), "criado_em": datetime(2026, 11, 7, 10, 30, tzinfo=timezone.utc).isoformat()}
texto = json.dumps(pedido, ensure_ascii=False)
print(texto)
volta = json.loads(texto)
print(volta["pago"], volta["desconto"], Decimal(volta["total"]), datetime.fromisoformat(volta["criado_em"]).year)
```
```text
{"id": 10, "pago": false, "desconto": null, "itens": [{"sku": "MS-01", "qtd": 2}], "total": "99.80", "criado_em": "2026-11-07T10:30:00+00:00"}
False None 99.80 2026
```
**4. Um servidor com cookies e sessão**
```python
import json
import secrets
import threading
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, HTTPServer

SESSOES = {}                       # id -> dados (em produção: banco/Redis)

class H(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    def log_message(self, *a): pass

    def responder(self, status, corpo, cookie=None):
        dados = json.dumps(corpo).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(dados)))
        if cookie:
            self.send_header("Set-Cookie", cookie)
        self.end_headers()
        self.wfile.write(dados)

    def sessao(self):
        c = SimpleCookie(self.headers.get("Cookie", ""))
        sid = c["sessionid"].value if "sessionid" in c else None
        return sid, SESSOES.get(sid)

    def do_POST(self):
        if self.path == "/login":
            sid = secrets.token_urlsafe(16)          # imprevisível!
            SESSOES[sid] = {"usuario": "ana", "carrinho": []}
            self.responder(200, {"ok": True},
                           f"sessionid={sid}; HttpOnly; SameSite=Lax; Path=/; Max-Age=3600")
        elif self.path == "/carrinho":
            _, dados = self.sessao()
            if dados is None:
                return self.responder(401, {"erro": "faça login"})
            dados["carrinho"].append("MS-01")
            self.responder(200, {"carrinho": dados["carrinho"]})

    def do_GET(self):
        _, dados = self.sessao()
        if dados is None:
            return self.responder(401, {"erro": "faça login"})
        self.responder(200, {"usuario": dados["usuario"], "carrinho": dados["carrinho"]})

srv = HTTPServer(("127.0.0.1", 8766), H)
threading.Thread(target=srv.serve_forever, daemon=True).start()
print("no ar")
```
```text
no ar
```
```bash
echo "# 1) sem cookie:"; curl -s -i http://127.0.0.1:8766/ | sed -n '1p;$p'
echo; echo "# 2) login (guarda cookie em jar.txt):"; curl -s -i -c jar.txt -X POST http://127.0.0.1:8766/login | grep -iE "^HTTP|set-cookie" | sed -E 's/sessionid=[^;]+/sessionid=<ALEATÓRIO>/'
echo "# 3) usando o cookie:"
curl -s -b jar.txt -X POST http://127.0.0.1:8766/carrinho; echo
curl -s -b jar.txt -X POST http://127.0.0.1:8766/carrinho; echo
curl -s -b jar.txt http://127.0.0.1:8766/; echo
```
```text
# 1) sem cookie:
HTTP/1.1 401 Unauthorized
{"erro": "fa\u00e7a login"}
# 2) login (guarda cookie em jar.txt):
HTTP/1.1 200 OK
Set-Cookie: sessionid=<ALEATÓRIO>; HttpOnly; SameSite=Lax; Path=/; Max-Age=3600
# 3) usando o cookie:
{"carrinho": ["MS-01"]}
{"carrinho": ["MS-01", "MS-01"]}
{"usuario": "ana", "carrinho": ["MS-01", "MS-01"]}
```
O servidor não tem memória por conexão: quem identifica o carrinho é o **cookie** que o `curl` reapresenta. Apague `jar.txt` e você “perde” a sessão.

**5. Por que o ID da sessão precisa ser imprevisível**
```python
import random
import secrets

random.seed(42)
print([random.randint(1000, 9999) for _ in range(3)], "← previsível se alguém descobrir a semente")
print(secrets.token_urlsafe(16), len(secrets.token_urlsafe(16)))
```
```text
[2824, 1409, 5506] ← previsível se alguém descobrir a semente
FwheuD1ake_2LdFJrclfRQ 22
```
IDs sequenciais (`1, 2, 3`) ou gerados com `random` podem ser adivinhados: quem adivinha o ID **é** o usuário (sequestro de sessão). Use `secrets`.

## ⚠️ Erros comuns e boas práticas
| Sintoma / mensagem | Causa | Solução |
|---|---|---|
| `SSL: CERTIFICATE_VERIFY_FAILED` | Certificado inválido, autoassinado ou CA ausente | Corrija o certificado; **nunca** desative a verificação em produção (`verify=False`) |
| Cookie não chega ao servidor | `Secure` em HTTP, `SameSite`, domínio/path diferente | Confira os atributos no DevTools (aula 04) |
| “Usuário deslogado sozinho” | Sessão expirou/reiniciou o servidor (memória) ou cookie sem `Max-Age` | Guarde a sessão em banco/Redis; ajuste a validade |
| Acentos viram `%C3%A3` ou `?` | Codificação de URL/charset | `urlencode`/`quote`; responda `charset=utf-8` |
| `json.JSONDecodeError: Expecting value` | Corpo vazio ou HTML de erro em vez de JSON | Cheque status e `Content-Type` antes do `json()` |
| Dados sensíveis na query string | Vão para logs, histórico, `Referer` | Envie por corpo/header |

- Sempre `HttpOnly; Secure; SameSite=Lax` em cookies de sessão (o Django faz isso por configuração: Módulo 9).
- Nunca guarde senhas ou dados sensíveis dentro do cookie; guarde só um ID aleatório.
- HTTPS em todo lugar, inclusive em desenvolvimento quando possível; HTTP só em `localhost`.

## 🧠 Pausa para lógica
**Problema (query string).** Implemente `parse_query(qs)` sem `urllib`: `"busca=mouse+gamer&cor=azul&cor=preto&vazio=&x=%C3%A9"` → `{"busca": ["mouse gamer"], "cor": ["azul", "preto"], "vazio": [""], "x": ["é"]}`.

<details><summary>Dica</summary>
Divida por <code>&amp;</code>, depois cada par por <code>=</code> (só a primeira ocorrência), troque <code>+</code> por espaço e decodifique os <code>%XX</code> com <code>bytes.fromhex</code> / <code>decode("utf-8")</code>.
</details>

<details><summary>Solução comentada</summary>

```python
import re
from collections import defaultdict
from urllib.parse import parse_qs

def decodificar(txt: str) -> str:
    txt = txt.replace("+", " ")
    # cada %XX vira um byte; depois todos os bytes são lidos como UTF-8
    bruto = re.sub(r"(?:%[0-9A-Fa-f]{2})+", lambda m: "".join(chr(b) for b in bytes.fromhex(m.group(0).replace("%", ""))), txt)
    return bruto.encode("latin-1").decode("utf-8")

def parse_query(qs: str) -> dict:
    out = defaultdict(list)
    for par in filter(None, qs.split("&")):
        chave, _, valor = par.partition("=")
        out[decodificar(chave)].append(decodificar(valor))
    return dict(out)

qs = "busca=mouse+gamer&cor=azul&cor=preto&vazio=&x=%C3%A9"
print(parse_query(qs))
print(parse_query(qs) == parse_qs(qs, keep_blank_values=True))
```
```text
{'busca': ['mouse gamer'], 'cor': ['azul', 'preto'], 'vazio': [''], 'x': ['é']}
True
```
A parte traiçoeira é o UTF-8: `%C3%A9` são **dois bytes** que juntos formam `é`. Na prática, use `urllib.parse`; implementar uma vez ajuda a entender por que `&` e `=` precisam ser codificados nos valores.
</details>

**Variação mais difícil:** o que acontece com `a=1&a=2` se você usar um `dict` simples (sobrescreve) em vez de lista? Como o Django expõe isso (`request.GET.getlist`)?

## 🧩 Exercícios
**1. Fixação**
Qual a diferença entre `Set-Cookie` e `Cookie`? Por que `HttpOnly` protege contra o roubo por XSS? O que o fragmento (`#...`) da URL envia ao servidor?

<details><summary>Solução</summary>

`Set-Cookie` é header de **resposta** (servidor cria/atualiza); `Cookie` é header de **requisição** (navegador devolve). Com `HttpOnly`, `document.cookie` não vê o cookie, então um script injetado não consegue lê-lo. O fragmento **não** é enviado ao servidor; é usado só pelo navegador.
</details>

**2. Aplicação no projeto MiniShop**
Estenda o servidor da aula 02 com um login simulado: `POST /login` (usuário e senha em JSON) cria uma sessão e devolve o cookie; `GET /me` devolve o usuário da sessão ou `401`; `POST /logout` apaga a sessão.

Critérios de pronto:
- [ ] ID de sessão com `secrets.token_urlsafe`
- [ ] Cookie com `HttpOnly; SameSite=Lax; Path=/; Max-Age=3600`
- [ ] Senha **não** aparece em logs nem na resposta
- [ ] Testado com `curl -c/-b`: login → `/me` → logout → `/me` (401)
- [ ] Commit `feat: add cookie session to the toy server`

<details><summary>Solução de referência</summary>

```python
# acrescente ao do_POST do servidor desta aula
elif self.path == "/logout":
    sid, dados = self.sessao()
    SESSOES.pop(sid, None)
    self.responder(204, {}, "sessionid=; Max-Age=0; Path=/")     # expira o cookie
# e em /login, valide credenciais de um dict {"ana": "senha-teste"} usando secrets.compare_digest
```
Use `secrets.compare_digest(a, b)` para comparar segredos (evita ataques por tempo). Armazenamento real de senhas (hash) é o tema do Módulo 9.
</details>

**3. Desafio (opcional)**
Implemente expiração: guarde `criada_em` e rejeite sessões com mais de 1 hora, apagando-as.

## 🎤 Na entrevista
- **O que é HTTPS e o que ele garante?** HTTP sobre TLS: confidencialidade (cifra), integridade (detecta alteração) e autenticidade do servidor (certificado assinado por uma CA confiável).
- **Como funciona uma sessão com cookie?** O servidor cria um ID aleatório, guarda os dados do usuário ligados a esse ID e envia o ID em `Set-Cookie`; o navegador o devolve a cada requisição e o servidor recupera os dados.
- **Para que servem `HttpOnly`, `Secure` e `SameSite`?** Bloquear leitura por JavaScript, exigir HTTPS e limitar envio em requisições entre sites (contra XSS, interceptação e CSRF).

## 📚 Para ir além
- 📄 Documentação oficial: [Cookies HTTP (MDN)](https://developer.mozilla.org/pt-BR/docs/Web/HTTP/Guides/Cookies). Atributos e boas práticas.
- 📄 Documentação oficial: [TLS no glossário (MDN, PT-BR)](https://developer.mozilla.org/pt-BR/docs/Glossary/TLS) e [Transport Layer Security (MDN, EN)](https://developer.mozilla.org/en-US/docs/Web/Security/Transport_Layer_Security). Conceitos de TLS para web.
- 📄 Documentação oficial: [`urllib.parse`](https://docs.python.org/3/library/urllib.parse.html) e [`secrets`](https://docs.python.org/3/library/secrets.html). Manipulação de URLs e geração segura de tokens.
- 📄 Documentação oficial: [JSON (MDN)](https://developer.mozilla.org/pt-BR/docs/Learn_web_development/Core/Scripting/JSON). Sintaxe e uso.
- 🏋️ Prática extra: em um site que você usa, abra o DevTools (aula 04) e liste os cookies, com seus atributos.

## ✅ Checklist da aula
- [ ] Vi o handshake e o certificado de um site real
- [ ] Decompus uma URL e codifiquei uma query string
- [ ] Reproduzi login com cookie usando `curl -c/-b`
- [ ] Sei dizer o que faz cada atributo de cookie
- [ ] Fiz o commit do exercício
