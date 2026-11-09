# Módulo 14 — Produção e observabilidade básica

> ⏱️ 5 sessões · 7.5 h · Pré-requisitos: Módulo 13 concluído (checkpoint aprovado).
> 🏷️ Marco no Git: `v4.1-producao`

## 🎯 Objetivos
- Emitir logs estruturados e expor health checks
- Monitorar erros com Sentry e métricas básicas
- Usar cache Redis com TTL e estratégia de invalidação
- Encontrar consultas lentas e planejar backups

## 📖 Aulas

| # | Aula | Tempo |
|---|------|-------|
| 01 | [Logs estruturados e health checks](01-logs-estruturados-health.md) | 1h30 |
| 02 | [Monitoramento de erros (Sentry) e métricas](02-sentry-metricas.md) | 1h30 |
| 03 | [Cache com Redis: TTL e invalidação](03-cache-redis.md) | 1h30 |
| 04 | [Performance (consultas lentas) e backups](04-performance-backups.md) | 1h30 |
| 05 | [Checkpoint](checkpoint.md) (quiz de 10 questões, entrega prática, autoavaliação) | 1h30 |

> Se uma aula pedir mais de uma sessão, ela é dividida em parte 1 e parte 2 na geração do módulo.

## 📦 Entrega do projeto
Endpoint `/health/`, logs JSON, Sentry configurado, cache no catálogo e procedimento de backup/restore testado.

## 🔗 Conexão com o próximo módulo
Próximo: [Módulo 15 — FastAPI (comparativo)](../15-fastapi-comparativo/README.md).

> ✅ Status: as 4 aulas e o checkpoint estão gerados. **Executado** com PostgreSQL 18.6 (200 mil produtos), Redis 8 e `uvicorn` locais; **341 testes**. **Sem conta Sentry** (testado com transporte falso) e sem Prometheus/Grafana. Referência em [`projeto/referencia-api-m14/`](../projeto/referencia-api-m14/README.md). Links conferidos com HTTP 200 em 2026-11-09.
