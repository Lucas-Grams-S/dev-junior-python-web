# Projeto de referência: MiniShop até o módulo 7 (e-mail assíncrono, agendamento, webhook, eventos e WebSocket)

Este é o **laboratório usado para executar e verificar** as aulas do módulo 7. Contém tudo do módulo 6 (API REST, JWT, permissões, filtros, OpenAPI, CORS, front-end) e acrescenta **Celery + Redis**, **tarefas idempotentes e agendadas**, **webhook de pagamento assinado**, **outbox + RabbitMQ** e **WebSocket (Django Channels)**. Use como **gabarito para comparar** com o seu projeto, não como substituto.

> ⚠️ **O que ele NÃO é:** não tem as telas HTML/Admin do módulo 5, usa **SQLite** (a concorrência real do pedido e o `skip_locked` do outbox exigem PostgreSQL) e o "gateway de pagamento" e o "SMTP" são **simulados**. Chaves e senhas são **só de laboratório**.

## Como rodar
```bash
uv sync                                   # Python 3.13 + dependências (uv.lock)
uv run python manage.py migrate
uv run python manage.py seed              # 64 produtos; usuários: gerente, estoquista, cliente (senha dev-somente-local-123)
uv run pytest -q                          # 97 testes (não precisam de Redis nem de RabbitMQ)
```
Os experimentos das aulas precisam de infraestrutura (as portas abaixo são as usadas no laboratório; ajuste `CELERY_BROKER_URL`, `REDIS_PORT` e a porta do `pika` se usar outras):
```bash
docker run -d --name m7-redis  -p 127.0.0.1:6390:6379 redis:8
docker run -d --name m7-rabbit -p 127.0.0.1:5680:5672 -p 127.0.0.1:15680:15672 rabbitmq:4-management
#   (se o RabbitMQ cair com "erlang.cookie: eacces", veja o quadro "Tropeço real" da aula 7.10)
uv run celery -A config worker -l info -c 2         # worker
uv run celery -A config beat -l info                # beat (UM só)
uv run gunicorn config.wsgi --threads 4             # API (WSGI)
uv run uvicorn config.asgi:application --port 8143  # WebSocket (ASGI)
```

## Mapa (módulo 7)
| Onde | Aula |
|---|---|
| `scripts/m7/io_cpu.py`, `classificar.py` | 7.01 |
| `scripts/m7/gil.py`, `race.py`, `overhead.py`, `django_threads.py`, `mini_pool.py` | 7.02 |
| `scripts/m7/aio1.py`, `aio2.py`, `aio_django.py`, `mini_loop.py`, `ant_async.py` | 7.03 |
| `scripts/m7/servidor_externo.py`, `hx1.py`, `hx2.py`, `hx3.py`, `breaker.py`, `ref_antifraude.py` | 7.04 |
| `config/wsgi.py`, `config/asgi.py`, `config/views_demo.py`, `scripts/m7/bench.py`, `wsgi_asgi.py`, `shed.py` | 7.05 |
| `config/celery.py`, `apps/orders/tasks.py`, `notifications.py`, `email_backend.py`, `scripts/m7/celery_demo.py`, `oncommit_demo.py`, `mini_broker.py` | 7.06 |
| `apps/orders/models.py` (`EmailLog`), `apps/orders/tasks.py` (reclamo, retentativas), `scripts/m7/retry_demo.py`, `claim.py` | 7.07 |
| `CELERY_BEAT_SCHEDULE` em `config/settings.py`, `scripts/m7/beat_demo.py`, `beat_catchup.py`, `cron.py` | 7.08 |
| `apps/payments/` (`security.py`, `services.py`, `api.py`), `scripts/m7/gateway_fake.py`, `webhook_demo.py`, `reducer.py` | 7.09 |
| `apps/payments/outbox.py`, `apps/realtime/`, `scripts/m7/rabbit_demo.py`, `outbox_demo.py`, `ws_demo.py`, `rele_sem_broker.py` | 7.10 |
| `tests/` | todas |

Os scripts de demonstração (`scripts/m7/*.py`) assumem a variável `LAB` apontando para a raiz do projeto (por exemplo `LAB=$PWD uv run python scripts/m7/celery_demo.py`) e dependem de `scripts/m7/servidor_externo.py` e `gateway_fake.py` (`PYTHONPATH=scripts/m7`). Os de módulos anteriores estão em `scripts/m6/`, `frontend/` e `e2e/`.
