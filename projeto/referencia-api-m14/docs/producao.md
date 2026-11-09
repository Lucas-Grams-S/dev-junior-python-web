# Operação do MiniShop em produção (runbook)

## Sinais que eu olho
| Pergunta | Onde |
|---|---|
| O processo está vivo? | `GET /health/` (200) |
| Consegue atender? | `GET /health/ready/` (200; 503 = banco ou cache) |
| Quanto erro/latência? | `/metrics/` (`minishop_http_requests_total`, `..._duration_seconds`) |
| O que quebrou? | Sentry (por `release`) e os logs JSON (`request_id`) |
| O cache ajuda? | `minishop_cache_requests_total{result}` e o cabeçalho `X-Cache` |

## Quando o Redis cai
Catálogo continua (sem cache, mais lento); limite de taxa geral falha **aberto**; **login responde 503** (falha fechada, de propósito). `/health/ready/` = 503.

## Backup e restauração
- Diário: `scripts/prod/backup.sh` (dump `-Fc`, SHA-256, faixa de contagens, retenção 7).
- Semanal: `scripts/prod/restore_test.sh` (restaura num banco temporário e compara). **Registre o tempo: é o seu RTO medido.**
- RDS: backups automáticos/PITR **além** do dump lógico.
