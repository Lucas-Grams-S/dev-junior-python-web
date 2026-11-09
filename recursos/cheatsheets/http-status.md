# Cheatsheet: HTTP

## Métodos
| Método | Seguro | Idempotente | Uso |
|---|---|---|---|
| GET / HEAD | sim | sim | ler / só headers |
| POST | não | não | criar / ação |
| PUT | não | sim | substituir |
| PATCH | não | em geral não | alterar parcialmente |
| DELETE | não | sim | remover |
| OPTIONS | sim | sim | o que é permitido (CORS) |

## Status
| Código | Quando |
|---|---|
| 200 OK · 201 Created (+`Location`) · 204 No Content | sucesso |
| 301 / 302 / 304 | redirecionamento permanente / temporário / não modificado |
| 400 | requisição malformada (JSON ruim, parâmetro inválido) |
| 401 | não autenticado (`WWW-Authenticate`) |
| 403 | autenticado, sem permissão |
| 404 | não existe |
| 405 | método não permitido (`Allow`) |
| 409 | conflito de estado (duplicado, estoque) |
| 413 / 415 | corpo grande demais / tipo de mídia não suportado |
| 422 | dados válidos no formato, inválidos nas regras |
| 429 | muitas requisições |
| 500 / 502 / 503 / 504 | erro interno / gateway ruim / indisponível / timeout do gateway |

## Headers frequentes
`Host` · `Content-Type` · `Content-Length` · `Accept` · `Authorization: Bearer ...` · `Location` · `Set-Cookie` / `Cookie` · `Cache-Control` · `User-Agent` · `Allow`

## curl
```bash
curl -s URL                         # corpo
curl -i URL                         # + headers da resposta
curl -v URL                         # requisição e resposta
curl -X POST URL --json '{"a":1}'   # POST JSON
curl -H "Authorization: Bearer T" URL
curl -c jar.txt -b jar.txt URL      # grava/usa cookies
curl -sL -o /dev/null -w '%{http_code} %{time_total}\n' URL
curl -fsS URL                       # falha em erro HTTP (para scripts)
```
