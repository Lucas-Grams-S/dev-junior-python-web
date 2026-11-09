# catalog-fastapi — catálogo do MiniShop em FastAPI (módulo 15)

Fatia do catálogo (lista, detalhe, criar, apagar, categorias) reimplementada em **FastAPI + SQLAlchemy 2 (async) + Pydantic 2 + Alembic**, para comparar com o Django/DRF do módulo 14. **Não** substitui o catálogo do Django (ver "O que falta").

## Rodar
```bash
uv sync
uv run alembic upgrade head              # cria as tabelas (SQLite local por padrão)
uv run python -m app.seed                # 64 produtos, os mesmos do seed do Django
CATALOG_API_TOKEN=segredo uv run uvicorn app.main:app --port 8815
# http://localhost:8815/docs
```
Configuração por variáveis `CATALOG_*` (`app/config.py`): `CATALOG_DATABASE_URL` (ex.: `postgresql+asyncpg://usuario:senha@host:5432/banco`), `CATALOG_API_TOKEN` (**vazio = escrita desligada**).

## Verificações (2026-11-09)
```bash
uv run pytest -q                          # 30 passed (SQLite em memória)
CATALOG_TEST_DATABASE_URL=postgresql+asyncpg://postgres:lab@127.0.0.1:55415/catalog_test uv run pytest -q   # 30 passed (PostgreSQL 18.6)
uv run ruff check . && uv run ruff format --check . && uv run mypy app
uv run python scripts/comparar.py http://localhost:8816 http://localhost:8815   # com o Django do módulo 14 no ar: 13 iguais, 3 diferentes
```

## Mapa
| Caminho | O que é |
|---|---|
| `app/main.py` | aplicação, `lifespan`, `/health/` e `/health/ready/` |
| `app/routers/products.py`, `categories.py` | rotas |
| `app/schemas.py` | Pydantic (`ProductIn`, `ProductOut`, `Page[T]`) |
| `app/models.py`, `app/db.py` | SQLAlchemy e sessão (dependência com `yield`) |
| `app/security.py`, `pagination.py`, `slug.py`, `config.py` | token de serviço, paginação, slug, configuração |
| `app/frete.py` | cliente `httpx` assíncrono de exemplo (aula 04) |
| `migrations/` | Alembic (`0001_tabelas_iniciais.py`; `server_default` corrigido para `sa.true()`) |
| `scripts/` | `hello.py`, `async_demo.py` + `medir_async.py`, `lazy_load_demo.py`, `comparar.py`, `carga.py` |
| `tests/` | 30 testes (API e cliente de frete) |

## O que falta (de propósito)
`PUT/PATCH`, imagem em S3, cache, throttling, métricas, logs JSON com `request_id`, usuários/JWT (só há um token de serviço), pedidos, `Dockerfile`/CI, e uma estratégia para conviver com o banco do Django. Os scripts de carga/async são didáticos (1 processo, mesma máquina).
