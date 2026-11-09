# Projeto de referência: API REST do MiniShop (módulo 6)

Este é o **laboratório usado para executar e verificar** as aulas 03 a 14 do módulo 6. Ele reproduz, em tamanho reduzido, os modelos e os serviços do MiniShop do módulo 5 (catálogo, carrinho, pedidos transacionais) e acrescenta a **API REST**, o **front-end** e os testes. Serve de **gabarito para comparar** com o seu projeto, não de substituto: construa o seu seguindo as aulas e consulte aqui quando algo divergir.

> ⚠️ **O que ele NÃO é:** não tem as telas HTML/Admin do módulo 5, usa SQLite (a concorrência real do pedido, aula 5.17, exige PostgreSQL) e as chaves/senhas são **só de laboratório**.

## Como rodar
```bash
uv sync                                   # Python 3.13 + dependências (uv.lock)
uv run python manage.py migrate
uv run python manage.py seed              # 64 produtos; usuários: gerente, estoquista, cliente (senha dev-somente-local-123)
uv run pytest -q                          # 65 testes
uv run python manage.py runserver 8131    # API em http://127.0.0.1:8131/api/v1/  ·  docs em /api/docs/
cd frontend && python3 -m http.server 8200 --bind 127.0.0.1    # front em http://127.0.0.1:8200  (origem liberada no CORS)
```
Checagens de entrega (as mesmas da aula 6.13):
```bash
uv run pytest --cov=apps -q
uv run python scripts/cobertura_de_rotas.py
uv run python manage.py check && uv run python manage.py makemigrations --check --dry-run
uv run python manage.py spectacular --validate --fail-on-warn > /dev/null
cd frontend && node --test test/api.test.js                    # 12 testes do cliente (Node 22)
cd e2e && npm i puppeteer-core && node e2e.mjs minishop.png    # E2E no Chrome (API e front no ar)
```

## Mapa
| Pasta/arquivo | Aula |
|---|---|
| `apps/*/models.py`, `services.py` | 5.04, 5.16, 5.17 (resumidos) |
| `apps/*/serializers.py` | 6.03 |
| `apps/*/api.py`, `config/api_urls.py` | 6.04, 6.07, 6.08, 6.13 |
| `config/errors.py`, `config/schemas.py` | 6.05, 6.10 |
| `apps/accounts/` (JWT, `/auth/me/`, throttle de login) | 6.06, 6.09 |
| `apps/catalog/filters.py`, `apps/orders/filters.py` | 6.08 |
| `config/pagination.py` | 6.09 |
| `schema.yml` | 6.10 (gerado por `manage.py spectacular`) |
| `config/settings.py` (CORS) | 6.11, 6.14 |
| `tests/`, `conftest.py` | 6.04–6.14 |
| `grpc_demo/` e `scripts/` | 6.13 e as pausas de lógica |
| `frontend/`, `e2e/` | 6.14 |
