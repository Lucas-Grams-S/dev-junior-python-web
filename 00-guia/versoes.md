# Versões usadas no treinamento

> Verificado em **2026-11-07** nas fontes primárias (python.org, djangoproject.com, postgresql.org, API JSON do PyPI, aws.amazon.com/free). Reverificar antes de gerar cada módulo.

| Tecnologia | Versão atual verificada | Versão adotada no curso | Observação |
|---|---|---|---|
| Python | 3.15.2 (lançado 2026-10-25; 3.15 saiu em 2026-10-09) | **3.13** (instalado via `uv`) | 3.13 tem suporte de segurança até 2029-10 e compatibilidade ampla com bibliotecas. 3.10 chegou ao fim da vida em 2026-10. Migrar para 3.14/3.15 é exercício opcional. |
| Django | 6.1.3 (requer Python ≥ 3.12) | **5.2 LTS** (5.2.19) | 5.2 é o único LTS suportado (extended support até abril/2028). **6.2 LTS sai em abril/2027**; o curso inclui nota de migração. |
| Django REST Framework | 3.18.3 (suporta Django 5.2, 6.0, 6.1) | 3.18.x | Compatível com Django 5.2. |
| FastAPI | 0.162.2 (Python ≥ 3.10) | 0.162.x | Ainda 0.x: APIs mudam; fixar versão no `uv.lock`. |
| SQLAlchemy | 2.1.8 | 2.1.x | Estilo 2.x (`select()`, `Mapped[...]`). |
| PostgreSQL | 18.6 (também 17.11, 16.15) | **18** (imagem `postgres:18`) | 14 sai de suporte em 2026-11-12. |
| pytest | 9.2.0 | 9.x | |
| ruff | 0.17.4 | 0.17.x | |
| uv | 0.13.7 | 0.13.x | |
| sentry-sdk / prometheus-client (Módulo 14) | 2.74.0 / última do lock | 2.x / 0.x | `send_default_pii` depreciada no 2.74: usar `data_collection`. |
| AWS CLI / boto3 / django-storages / moto | 2.39.5 / 1.43.126 / 1.14.6 / 5.2.5 (usados no Módulo 13) | mesmas | `moto` simula a AWS; a conta real não foi usada. Planos e preços da AWS: ler a documentação no dia. |
| GitHub Actions (SHAs fixados no módulo 12) | actions/checkout v7.0.1, astral-sh/setup-uv v10.3.3, docker/setup-buildx-action v4.4.1, docker/build-push-action v7.4.0, docker/login-action v4.8.0, docker/metadata-action v6.2.0 | mesmas | Conferidas pela API do GitHub em 2026-11-08; o Dependabot atualiza. |
| Docker / Compose | Docker Engine 29.9.2 e Compose v5.6.1 (versões **instaladas e usadas** para testar o Módulo 3 em 2026-11-07; página de releases não verificada) | Docker atual; imagem `postgres:18` (PostgreSQL 18.6) | Módulo 11 usou as mesmas versões (Docker 29.9.2, Compose v5.6.1) e imagens `python:3.13-slim` (3.13.18), `postgres:18` (18.6), `redis:8`, `nginx:1.29-alpine` e `ghcr.io/astral-sh/uv:0.9`, Gunicorn 26.2.0 e Uvicorn 0.54.0; testadas em 2026-11-08. |
| psycopg | 3.3.8 (`psycopg[binary]`) | 3.3.x | |
| Redis | 8.10.3 (imagem `redis:8`, testada localmente em 2026-11-07) | 8.x | Docker Hub; verificar a tag mais nova no Módulo 7. |
| Django (usado no Módulo 3 só como biblioteca de ORM) | 5.2.19 | 5.2 LTS | |
| Node.js | 22.22.1 (instalado e usado nos testes do Módulo 4) | 22 LTS | `node --test` e `fetch` nativos. |
| Chrome / Chromium | 156.0 (headless, usado para testar HTML/CSS/JS do Módulo 4) | atual | Qualquer navegador moderno serve ao aluno. |
| htmx · Vue · React · axe-core (via CDN com SRI) | 2.0.4 · 3.5.13 · 18.3.1 · 4.10.2 | versões fixas | Fixar versão e usar `integrity` (SRI). |
| AWS Free Tier | Modelo novo: **US$ 100 em créditos ao abrir a conta, até US$ 200 ao explorar serviços; expira em 6 meses** | Plano gratuito (*Free plan*) | EC2, RDS, S3 entram; “Paid plan” cobra pay-as-you-go. Não é mais “12 meses de t2.micro”. Detalhes no Módulo 13. |

## Pendências de verificação
- Datas exatas de lançamento de cada pacote (a API JSON do PyPI veio truncada).
- Suporte oficial do Django 5.2 ao Python 3.14/3.15.
- Versões de Docker/Compose, Redis, Celery, Gunicorn, Sentry SDK, Node (Módulo 4).

## Reverificação para o módulo 6 (2026-11-08, PyPI)
| Pacote | Versão | Django suportado |
|---|---|---|
| djangorestframework | 3.18.3 | 5.2, 6.0, 6.1 |
| djangorestframework-simplejwt | 5.5.1 | até 5.2 (classificadores do PyPI) |
| drf-spectacular | 0.30.0 | conferir no `uv add` |
| django-filter | 26.2 (Python ≥ 3.11) | conferir no `uv add` |
| django-cors-headers | 4.9.0 | conferir no `uv add` |

## Reverificação para o módulo 7 (2026-11-08, PyPI)
| Pacote | Versão | Observação |
|---|---|---|
| celery | 5.7.0 | broker Redis; Python ≥ 3.10 |
| redis (redis-py) | 8.1.0 | servidor Redis 8 (imagem `redis:8`) |
| httpx | 0.28.1 | cliente síncrono e assíncrono |
| gunicorn / uvicorn | 26.2.0 / 0.54.0 | usados nos experimentos |
| channels / channels-redis | 4.3.2 / 4.3.0 | `channels.testing` exige `daphne` |
| pika | 1.4.4 | cliente RabbitMQ (imagem `rabbitmq:4-management`, 4.4) |
| websockets | 17.4 | cliente usado no experimento |

## Módulo 8 (laboratório de 2026-11-08, `uv pip list`)
| Pacote | Versão usada | Observação |
|---|---|---|
| import-linter / grimp | 2.16 / 3.19 | contratos `layers` e `forbidden`; grafo de imports |
| mypy | 2.4.1 | verifica `Protocol` |
| radon | 6.0.1 | complexidade ciclomática, linhas, manutenibilidade |
| ruff | 0.17.4 | regras `C901`, `S608`, `PLR0912`, `PLW0603` |
| coverage / pytest-cov | 7.17.2 / 7.1.0 | cobertura de ramos do legado |
| pytest-env | 1.8.5 | variáveis de ambiente do `pytest.ini` |
| psycopg | 3.3.8 | PostgreSQL 18.6 (imagem `postgres:18`, contêiner próprio) |
| gunicorn | 26.2.0 | teste de `SIGTERM` gracioso (docs em gunicorn.org) |

## Módulo 9 (laboratório de 2026-11-08)
| Item | Versão usada | Observação |
|---|---|---|
| OWASP Top 10 | 2025 | a página oficial redireciona para a edição de 2025 |
| argon2-cffi / bcrypt | 25.1.0 / 5.0.0 | Argon2id é o primeiro de `PASSWORD_HASHERS` |
| bandit | 1.9.4 | regras `B*`; o `ruff` cobre as equivalentes `S*` |
| pip-audit / detect-secrets | 2.10.1 / 1.5.0 | `detect-secrets` precisa de `--all-files` fora de um repositório Git |
| OpenSSL | 3.5.5 | CA e certificado de laboratório |
| Gunicorn | 26.2.0 | TLS direto (`--certfile`/`--keyfile`) e 2 workers |
| PostgreSQL | 18.6 | papéis dono/aplicação/leitura |
| Redis | 8 | cache compartilhado do throttling |

## Módulo 10 (laboratório de 2026-11-08)
| Item | Versão usada | Observação |
|---|---|---|
| pytest · pytest-django | 9.x · ver `uv.lock` | marcadores `unidade`/`integracao`/`api` |
| pytest-randomly · pytest-xdist · pytest-env · pytest-cov | 5.0.0 · 3.8.0 · 1.8.5 · 7.1.0 | ordem aleatória, paralelismo, variáveis, cobertura |
| ruff | 0.17.4 | lint + formatação; `line-length = 140` |
| mypy · django-stubs · djangorestframework-stubs | 2.4.1 · 6.1.2 · 3.18.2 | adoção gradual |
| pre-commit | 4.7.0 | hooks locais (versões do `uv.lock`) |
| commitizen | 4.19.3 | valida Conventional Commits, calcula versão e changelog |
| celery-types · types-channels · types-django-filter | ver `uv.lock` | stubs de tipos |

## Módulo 15 (laboratório de 2026-11-09, `uv pip list`, Python 3.13.18)
| Pacote | Versão |
|---|---|
| fastapi · starlette · uvicorn | 0.162.2 · 1.10.0 · 0.54.0 |
| pydantic · pydantic-core · pydantic-settings | 2.14.3 · 2.50.4 · 2.16.2 |
| sqlalchemy · alembic | 2.1.8 · 1.20.1 |
| aiosqlite · asyncpg | 0.22.1 · 0.32.0 |
| httpx · pytest · pytest-asyncio | 0.28.1 · 9.2.0 · 1.4.1 |
| ruff · mypy | 0.17.4 · 2.4.1 |
| Flask · Werkzeug (só um exemplo mínimo) | 3.1.3 · 3.1.9 |
| PostgreSQL (contêiner descartável) | 18.6 |

Notas: o serviço fixa as versões no `uv.lock`; `Page[T]` usa a sintaxe de genéricos do Python ≥ 3.12; o status HTTP 422 usa `status.HTTP_422_UNPROCESSABLE_CONTENT` (nome atual na Starlette 1.x).

## Módulo 16 (verificado em 2026-11-09)
`projeto/referencia-m16`: Python 3.13.x, `fastapi`, `httpx`, `uvicorn`, `pytest`, `ruff` (versões exatas fixadas no `uv.lock`); Git 2.53.0; SQLite do módulo `sqlite3` do Python. Aviso: `starlette.testclient` com `httpx` emite `StarletteDeprecationWarning` (sugere `httpx2`).
