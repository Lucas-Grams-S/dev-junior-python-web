# Cheatsheet: concorrência, Celery, filas e tempo real (módulo 7)

> Aulas 7.01 a 7.10. Tudo foi executado no laboratório [`projeto/referencia-api-m7`](../../projeto/referencia-api-m7/README.md).

## Escolher a ferramenta
| Problema | Ferramenta |
|---|---|
| esperar várias vezes (rede/banco) | `asyncio` (+ `httpx.AsyncClient`) ou `ThreadPoolExecutor` |
| cálculo pesado | `ProcessPoolExecutor` (ou algoritmo/biblioteca em C) |
| trabalho que pode esperar (e-mail, relatório) | **fila + worker** (Celery) |
| avisar quando algo acontece em outro sistema | **webhook** (assinado, idempotente) |
| vários interessados no mesmo fato | **mensageria** (RabbitMQ/SQS) + **outbox** |
| mostrar mudança ao usuário na hora | **WebSocket** (Channels) ou SSE |
| tarefa recorrente | **Celery beat** (um só) / cron / CronJob |

## Medir antes de otimizar
`time.perf_counter()` = parede · `time.process_time()` = CPU · razão ≈ 0 → espera; ≈ 1 → cálculo · vazão por worker = `1 / latência`.

## Threads, processos, GIL
- GIL: uma thread executa bytecode por vez → threads ajudam **esperas**, não cálculo (Python com GIL).
- Processos: `ProcessPoolExecutor` (use `chunksize` em tarefas pequenas; `if __name__ == "__main__":`).
- Corrida: `x += 1` não é atômico → `threading.Lock`, `queue.Queue`, ou `F()`/`select_for_update()` no banco.
- Django: **uma conexão por thread**; threads suas devem chamar `connections.close_all()`.

## asyncio
```python
await asyncio.gather(*(chamar(u) for u in urls))          # esperas sobrepostas
async with asyncio.TaskGroup() as tg: tg.create_task(...)  # falhou uma → cancela as irmãs
async with asyncio.timeout(1): await ...                  # limite de tempo
sem = asyncio.Semaphore(5); async with sem: ...           # limita a concorrência
await asyncio.to_thread(funcao_bloqueante, arg)           # NUNCA time.sleep/requests dentro de async def
await Model.objects.aget(...); await sync_to_async(servico)(...)   # ORM assíncrono / serviço síncrono
```

## httpx (timeouts e retentativas)
```python
with httpx.Client(base_url=URL, timeout=httpx.Timeout(5, read=2)) as c: ...    # um Client compartilhado
# repetir: falha de rede/timeout, 429 (respeite Retry-After), 502/503/504; NÃO repetir 4xx; POST só com Idempotency-Key
# espera = min(teto, base * 2**n) * random()   (backoff exponencial com jitter)
httpx.Client(transport=httpx.MockTransport(funcao))   # testar sem rede
```

## Servidores
```bash
gunicorn config.wsgi --workers 4 --threads 4 --timeout 30 --max-requests 1000     # WSGI
uvicorn config.asgi:application --workers 4                                        # ASGI (WebSockets/async)
```
`async def` sob WSGI **não** dá concorrência. Nginx na frente (TLS, estáticos, clientes lentos).

## Celery
```python
@shared_task(bind=True, autoretry_for=(ErroTransitorio,), retry_backoff=1, retry_backoff_max=30,
             retry_jitter=True, retry_kwargs={"max_retries": 4}, acks_late=True, soft_time_limit=20)
def tarefa(self, order_id): ...                 # recebe IDs; recarrega; é IDEMPOTENTE
transaction.on_commit(lambda: tarefa.delay(order.pk))        # enfileire SÓ depois do commit
```
```bash
celery -A config worker -l info -c 4 [-Q emails]      # execução
celery -A config beat -l info --schedule /dados/celerybeat-schedule   # UM beat só
celery -A config inspect registered | active           # diagnóstico
```
```python
CELERY_BEAT_SCHEDULE = {"x": {"task": "orders.x", "schedule": crontab(minute="*/15")}}   # UTC; teste: toda tarefa existe em app.tasks
```
Cron: `min hora dia mês dia_da_semana` (`*/15 * * * *`, `0 3 * * *`, `30 8 * * 1-5`).

## Idempotência (consumidor)
`UNIQUE(event_id)` + registro de execução; **reclamo atômico** (`UPDATE ... WHERE status='pending'` → 1 linha); estado que **só avança**; chave de idempotência do provedor; falha permanente ≠ transitória; desistência registrada (`on_failure`).

## Webhook (receber)
`X-Signature: t=<ts>,v1=HMAC_SHA256(segredo, f"{ts}.{corpo_bruto}")` → verificar **bytes brutos**, `hmac.compare_digest`, tolerância 5 min, `event_id` único, validar valor/estado no **seu** banco, `2xx` rápido, fila para o resto.

## RabbitMQ (pika) e outbox
`exchange (topic) → binding (order.*, #) → fila durável` · `delivery_mode=2` · `basic_qos(prefetch_count=1)` · `basic_ack` depois de processar · `nack(requeue=False)` → DLQ · `confirm_delivery()` + `mandatory=True`.
**Outbox:** evento na mesma transação do estado → relé publica → consumidor deduplica por `message_id`.

## WebSocket (Channels)
`ProtocolTypeRouter({"http": ..., "websocket": JWTQueryMiddleware(URLRouter(...))})` · consumer autoriza por dono no `connect()` · `CHANNEL_LAYERS` com **Redis** em produção · `transaction.on_commit` para empurrar · envie o **estado atual** ao conectar.
