# MiniShop

[![CI](https://github.com/SEU-USUARIO/minishop/actions/workflows/ci.yml/badge.svg)](https://github.com/SEU-USUARIO/minishop/actions)
🇧🇷 Português · [🇺🇸 English](README.en.md)

API de uma loja virtual em **Django + DRF**: catálogo com busca, carrinho, pedidos com controle de estoque transacional, pagamento simulado por webhook assinado e e-mail assíncrono (Celery + Redis).

> Projeto de estudo: o gateway de pagamento é simulado e nenhum dado é real.

![Documentação interativa da API](docs/img/swagger.png)  <!-- print REAL do seu /api/docs/ -->

## O que ele demonstra
- Pedido com **baixa de estoque dentro de uma transação** e `Idempotency-Key` (repetir a requisição não duplica o pedido)
- **Webhook** com HMAC, proteção contra replay e idempotência
- **341 testes** (pirâmide: unitários, API, integração) em SQLite e PostgreSQL; `ruff` e `mypy` na CI
- **Docker Compose** (Nginx, web, worker, PostgreSQL, Redis), **GitHub Actions**, logs JSON e `/health/`

## Rode em 3 comandos
```bash
git clone https://github.com/SEU-USUARIO/minishop && cd minishop
uv sync && export DEBUG=1
uv run python manage.py migrate && uv run python manage.py seed && uv run python manage.py runserver
```
Abra `http://127.0.0.1:8000/api/docs/`. Testes: `uv run pytest`.

## Decisões técnicas
| Decisão | Por quê | Alternativa descartada |
|---|---|---|
| PostgreSQL | transações e `SELECT … FOR UPDATE` no estoque | SQLite (sem concorrência de escrita) |
| Pagamento atrás de uma porta (`PaymentGateway`) | trocar o provedor sem mexer no domínio | chamar o SDK direto na view |
| JWT curto (15 min) + refresh com rotação | API consumida por front-end separado | sessão por cookie |

Detalhes e ADRs em [`docs/adr/`](docs/adr/).

## Limitações conhecidas
- Pagamento e e-mail são simulados; sem conta Sentry/AWS reais neste repositório.
- Sem front-end completo (há uma página de demonstração).

## Autor
Seu Nome · [LinkedIn](https://www.linkedin.com/in/seu-perfil) · seu@email.com
