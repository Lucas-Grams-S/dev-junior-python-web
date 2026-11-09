# Mapa do módulo 14 (material do curso)

Laboratório do módulo 14: o projeto do módulo 13 com **observabilidade**, **cache** e **backup/restauração**.
Verificado com PostgreSQL 18.6 e Redis 8 em contêineres (nomes únicos, portas altas) e `uvicorn` local; o Sentry foi verificado **sem rede** (transporte falso): nenhuma conta Sentry foi usada.

| Onde | Aula |
|---|---|
| `config/logging_json.py`, `config/middleware.py`, `config/health.py`, `config/urls.py`, `config/healthcheck.py`, `tests/test_observabilidade.py` | 14.01 |
| `config/observability.py` (Sentry), `config/metrics.py` (Prometheus), `tests/test_sentry.py`, `tests/test_observabilidade.py` | 14.02 |
| `apps/catalog/cache.py`, `apps/catalog/signals.py`, `apps/catalog/api.py`, `config/throttling.py`, `tests/test_cache_catalogo.py` | 14.03 |
| `apps/catalog/models.py` (índice) + migração `0003`, `scripts/prod/{pgcli,backup,restore_test}.sh` | 14.04 |
| `deploy/compose.prod.yaml`, `deploy/nginx.conf` (resolver, `X-Request-ID`, `/metrics/` oculto) | 14.01 a 14.03 |

Backup e teste de restauração (precisam de Docker ou do cliente PostgreSQL):
`bash scripts/prod/backup.sh "$DATABASE_URL" ./backups 7 && bash scripts/prod/restore_test.sh "$DATABASE_URL" ./backups`
