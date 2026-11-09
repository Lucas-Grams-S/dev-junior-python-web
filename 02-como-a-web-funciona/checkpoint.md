# Checkpoint — Módulo 2: Como a web funciona

> ⏱️ ~1h30 · Faça **sem consultar** as aulas na primeira tentativa. 30 min para o quiz, 60 min para a entrega.

## 📝 Quiz (10 questões)
1. Descreva, em ordem, o que acontece desde digitar `https://loja.com.br/produtos` até o servidor receber a requisição HTTP.
2. Qual a diferença entre `Connection refused` e `timed out`? Dê uma causa provável de cada.
3. Por que o TCP é chamado de “fluxo de bytes” e como o HTTP resolve a delimitação das mensagens?
4. Para cada método, diga se é seguro e idempotente: `GET`, `POST`, `PUT`, `PATCH`, `DELETE`.
5. Que status code você usaria para: criar um recurso; recurso inexistente; usuário não logado; logado sem permissão; SKU duplicado; erro inesperado no servidor?
6. O que o HTTPS garante e o que é um certificado? Por que nunca usar `verify=False` em produção?
7. Decomponha `https://ana@loja.com:8443/p/42?cor=azul&cor=preto#fotos`. O que vai ao servidor?
8. Como funciona uma sessão com cookie? Para que servem `HttpOnly`, `Secure` e `SameSite`?
9. Dê duas diferenças entre sessão no servidor e token no cabeçalho `Authorization`.
10. Você tem uma chamada que funciona no navegador e falha no `curl`. Quais passos de investigação você faz? O que o TTFB alto indica?

<details><summary>Gabarito</summary>

1. Resolução DNS (cache/resolver → IP) → conexão TCP (handshake, porta 443) → handshake TLS (certificado validado, chaves) → requisição HTTP cifrada (`GET /produtos` + headers).
2. *Refused*: o host respondeu que ninguém atende na porta (servidor desligado, porta errada). *Timeout*: nenhuma resposta (firewall/Security Group descartando, host fora do ar ou rota inexistente).
3. TCP entrega bytes em ordem sem preservar fronteiras de mensagem; HTTP delimita com linha em branco após os headers e `Content-Length` (ou *chunked*) para o corpo.
4. GET: seguro e idempotente. POST: nenhum dos dois. PUT: idempotente, não seguro. PATCH: não seguro, em geral não idempotente. DELETE: idempotente, não seguro.
5. 201 (com `Location`); 404; 401; 403; 409 (ou 422); 500.
6. Cifra os dados, detecta alteração e autentica o servidor. Certificado liga um domínio a uma chave pública, assinado por uma CA confiável. Sem verificação, qualquer um se passa pelo servidor (ataque *man-in-the-middle*).
7. Esquema `https`, usuário `ana`, host `loja.com`, porta `8443`, caminho `/p/42`, query `cor=azul&cor=preto` (chave repetida = lista), fragmento `fotos`. O fragmento **não** vai ao servidor.
8. Servidor cria ID aleatório, guarda os dados ligados a ele e envia `Set-Cookie`; o navegador devolve `Cookie` a cada requisição. `HttpOnly`: JS não lê; `Secure`: só HTTPS; `SameSite`: limita envio cross-site (CSRF).
9. Sessão: estado no servidor, fácil de revogar, ideal para sites com HTML. Token: estado no cliente (assinado), servidor sem memória, difícil de revogar antes de expirar, ideal para APIs/apps móveis.
10. Copiar a requisição do DevTools (“Copy as cURL”) e comparar cookies, `Authorization`, `Origin`, `User-Agent` e `Accept`; ver o corpo de erro e o status; checar logs do servidor. TTFB alto indica lentidão de processamento no servidor (código/banco), não de rede.
</details>

## 🛠️ Entrega prática
Repositório `minishop` na tag `v0.2-http-minimo`:
- [ ] Pacote `minishop_http/` (`roteador`, `app`, `servidor`, `__main__`) servindo o estoque da CLI
- [ ] Rotas: `GET /saude`, `GET/POST /produtos`, `GET /produtos/<sku>`, `POST /produtos/<sku>/retirar`, `DELETE /produtos/<sku>`
- [ ] Erros em JSON com 400, 404, 405 (+`Allow`), 409, 422 e 500 (sem vazar detalhes)
- [ ] `uv run pytest -q` verde (CLI + HTTP, ≥ 36 testes)
- [ ] `docs/http-exemplos.md` (contrato desenhado à mão, aula 02) e `docs/testando-a-api.md` com `scripts/smoke.sh`
- [ ] Coleção Bruno (`api-collection/`) sem segredos
- [ ] `docs/arquitetura-http.md` com o diagrama de sequência
- [ ] Tag publicada: `git tag v0.2-http-minimo && git push --tags`

**Prova de fogo (30 min):** sem consultar, acrescente `PATCH /produtos/<sku>` que altera só o preço (validando `Decimal` ≥ 0), com teste cobrindo 200, 404 e 422.

## 🪞 Autoavaliação
Nota de 0 a 3. Se algum item ficar em **0 ou 1**, refaça a aula antes de seguir.

| Habilidade | Aula | Nota |
|---|---|---|
| Explicar IP, porta, DNS, TCP | 01 | |
| Escrever uma requisição/resposta HTTP à mão | 02 | |
| Escolher método e status code | 02 | |
| Explicar TLS, certificados e cookies/sessão | 03 | |
| Manipular URLs, query strings e JSON | 03 | |
| Depurar com DevTools e `curl` | 04 | |
| Medir DNS/TCP/TLS/TTFB | 04 | |
| Servidor HTTP mínimo com rotas e erros | 05 | |

## 🧠 Lógica: lista de verificação
Resolveu sem olhar: IP/CIDR com bits (01), parser de requisição HTTP (02), `parse_query` com UTF-8 (03), latência média vs p95 (04), roteamento por segmentos e prioridade (05)? Marque o que faltou e refaça.

➡️ Próximo: [Módulo 3 — Bancos de dados relacionais](../03-banco-de-dados/README.md).
