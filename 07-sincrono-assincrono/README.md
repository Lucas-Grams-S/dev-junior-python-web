# Módulo 7 — Comunicação síncrona e assíncrona

> ⏱️ 11 sessões · 16.5 h · Pré-requisitos: Módulo 6 concluído (checkpoint aprovado).
> 🏷️ Marco no Git: `v2.1-async-email-webhook`

## 🎯 Objetivos
- Diferenciar I/O-bound e CPU-bound e escolher threads, processos ou asyncio
- Explicar o GIL e por que `async` melhora a espera, não a velocidade bruta
- Chamar APIs externas com `httpx`, timeouts e retentativas
- Enviar e-mail de confirmação via fila (Celery + Redis) de forma idempotente
- Receber webhooks de pagamento simulado com segurança

## 📖 Aulas

| # | Aula | Tempo |
|---|------|-------|
| 01 | [Bloqueante vs não bloqueante; I/O-bound vs CPU-bound](01-bloqueante-io-cpu.md) | 1h30 |
| 02 | [Threads, processos e o GIL](02-threads-processos-gil.md) | 1h30 |
| 03 | [`asyncio` e `async`/`await`](03-asyncio.md) | 1h30 |
| 04 | [`httpx`, timeouts e retentativas](04-httpx-timeouts-retries.md) | 1h30 |
| 05 | [WSGI vs ASGI](05-wsgi-asgi.md) | 1h30 |
| 06 | [Filas e tarefas em segundo plano (Celery + Redis)](06-filas-celery.md) | 1h30 |
| 07 | [Retentativas e idempotência](07-retentativas-idempotencia.md) | 1h30 |
| 08 | [Agendamento de tarefas](08-agendamento.md) | 1h30 |
| 09 | [Webhooks: pagamento simulado](09-webhooks.md) | 1h30 |
| 10 | [Mensageria (RabbitMQ/SQS), eventos e WebSockets](10-mensageria-websockets.md) | 1h30 |
| 11 | [Checkpoint](checkpoint.md) (quiz de 10 questões, entrega prática, autoavaliação) | 1h30 |

> Se uma aula pedir mais de uma sessão, ela é dividida em parte 1 e parte 2 na geração do módulo.

## 📦 Entrega do projeto
**E-mail de confirmação assíncrono** (Celery + Redis) e **webhook de pagamento simulado** que muda o pedido para `paid`.

## 🔗 Conexão com o próximo módulo
Próximo: [Módulo 8 — Estrutura de projetos e arquitetura](../08-arquitetura/README.md).

> ✅ Status: as 10 aulas e o checkpoint estão gerados. **Todo o código foi executado** num laboratório (Python 3.13, Django 5.2.19; Celery 5.7 com worker e beat reais, Redis 8, RabbitMQ 4.4, Gunicorn, Uvicorn, Django Channels; 97 testes), reproduzido em [`projeto/referencia-api-m7/`](../projeto/referencia-api-m7/README.md). Links de “Para ir além” conferidos com HTTP 200 em 2026-11-08. Não executado: Amazon SQS, Kafka e serviços de nuvem (dados do SQS vêm da documentação oficial) e os desafios opcionais; o banco do laboratório é SQLite.
