# MiniShop

[![CI](https://github.com/YOUR-USER/minishop/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR-USER/minishop/actions)
[🇧🇷 Português](README.md) · 🇺🇸 English

An e-commerce API built with **Django + DRF**: searchable catalog, cart, orders with transactional stock control, simulated payments via signed webhooks, and asynchronous e-mail (Celery + Redis).

> Learning project: the payment gateway is simulated and no data is real.

## What it demonstrates
- Orders that **decrement stock inside a transaction**, with an `Idempotency-Key` (retrying a request does not create a second order)
- **Webhooks** with HMAC signatures, replay protection and idempotency
- **341 tests** on SQLite and PostgreSQL; `ruff` and `mypy` run in CI
- **Docker Compose** (Nginx, web, worker, PostgreSQL, Redis), **GitHub Actions**, JSON logs and a `/health/` endpoint

## Run it in three commands
```bash
git clone https://github.com/YOUR-USER/minishop && cd minishop
uv sync && export DEBUG=1
uv run python manage.py migrate && uv run python manage.py seed && uv run python manage.py runserver
```
Open `http://127.0.0.1:8000/api/docs/`. Tests: `uv run pytest`.

## Design decisions
| Decision | Why | Rejected alternative |
|---|---|---|
| PostgreSQL | transactions and `SELECT … FOR UPDATE` on stock | SQLite (single writer) |
| Payment behind a port (`PaymentGateway`) | swap providers without touching the domain | calling the SDK from the view |
| Short-lived JWT (15 min) + rotating refresh | API used by a separate front end | cookie sessions |

## Known limitations
- Payments and e-mail are simulated; no real Sentry/AWS account is used in this repository.
- No full front end (there is a demo page).

## Author
Your Name · [LinkedIn](https://www.linkedin.com/in/your-profile) · you@email.com
