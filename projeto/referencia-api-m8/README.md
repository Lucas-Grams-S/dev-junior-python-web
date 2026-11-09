# Projeto de referência: MiniShop até o módulo 8 (camadas, adaptadores, twelve-factor e legado refatorado)

Este é o **laboratório usado para executar e verificar** as aulas do módulo 8. Contém tudo do módulo 7 (API REST, JWT, e-mail assíncrono, webhooks, outbox, WebSocket) e acrescenta a **refatoração em camadas**, o **Adapter do gateway de pagamento**, a **configuração por ambiente** e o **legado refatorado**, com **ADRs** em `docs/adr/`.

> ⚠️ **O que ele NÃO é:** não tem as telas HTML/Admin do módulo 5; o gateway "Acme Pay" é um servidor **simulado escrito para o curso** (nenhum provedor real); o banco padrão é **SQLite**, e o PostgreSQL 18 foi usado via `DATABASE_URL` num contêiner à parte.

## Como rodar
```bash
uv sync                                   # Python 3.13 + dependências (uv.lock)
DEBUG=1 uv run python manage.py migrate
DEBUG=1 uv run python manage.py seed      # 64 produtos; usuários: gerente, estoquista, cliente (senha dev-somente-local-123)
uv run pytest -q                          # 146 passed, 1 skipped em SQLite (não precisam de Redis nem de RabbitMQ)
uv run lint-imports                       # 3 contratos de arquitetura
```
`DEBUG` é **falso por padrão** (twelve-factor): sem `DEBUG=1` e sem `SECRET_KEY`, o Django recusa subir. O `pytest.ini` já define `DEBUG=1`.

Em **PostgreSQL** (a paridade com produção; veja a aula 8.06):
```bash
docker run -d --name m8-pg18 -e POSTGRES_PASSWORD=lab -e POSTGRES_DB=minishop_m8 -p 127.0.0.1:5499:5432 postgres:18
export DEBUG=1 DATABASE_URL=postgres://postgres:lab@127.0.0.1:5499/minishop_m8
uv run python manage.py migrate && uv run pytest -q        # 143 passed, 4 skipped (o legado só roda em SQLite)
```

## Mapa (módulo 8)
| Onde | Aula |
|---|---|
| `apps/orders/domain.py`, `services.py`, `selectors.py`, `repositories.py`, `idempotency.py`, `.importlinter`, `scripts/m8/grafo.py`, `mistura.py`, `checa_camadas.py` | 8.01, 8.02 |
| `tests/test_pedido_dominio.py`, `tests/test_contrato_repositorio.py`, `scripts/m8/uow_demo.py`, `rapido_vs_banco.py` | 8.02 |
| `scripts/m8/ocp.py`, `ocp_smell.py`, `isp.py`, `lsp.py`, `duplicados.py`, `frete_*.py`, `yagni.py` | 8.03 |
| `apps/payments/gateway.py`, `tests/test_gateway.py`, `scripts/m8/servidor_acme.py`, `acme_demo.py` | 8.04 |
| `scripts/m8/chamada.py`, `.importlinter`, `docs/adr/0002-monolito-modular.md` | 8.05 |
| `config/envconf.py`, `config/settings.py`, `tests/test_envconf.py`, `tests/test_concorrencia.py`, `scripts/m8/sigterm.sh`, `lenta_wsgi.py`, `.env.example`, `docs/adr/0003-*.md` | 8.06 |
| `legado/pedidos_legado.py`, `legado/precificacao.py`, `tests/test_legado_*.py`, `tests/test_precificacao.py`, `tests/golden/legado.json`, `scripts/m8/legado_original_v0.py` | 8.07 |
| `scripts/m8/saidas/` | as saídas reais coladas nas aulas |

Os scripts de `scripts/m8/` assumem `LAB` apontando para a raiz do projeto e `PYTHONPATH=scripts/m8`, por exemplo `LAB=$PWD PYTHONPATH=scripts/m8 uv run python scripts/m8/grafo.py`. Alguns precisam de portas livres (`acme_demo.py` usa a 8150).

## Para refazer o golden master do legado
```bash
GOLDEN=gravar uv run pytest tests/test_legado_caracterizacao.py      # grava tests/golden/legado.json (270 casos)
uv run pytest tests/test_legado_caracterizacao.py                    # confere
```
`scripts/m8/legado_original_v0.py` é o legado **antes** da refatoração (para comparar).

## Estado de verificação
Executado em 2026-11-08 (Python 3.13, Django 5.2.19). Não executado: provedor de pagamento real, nuvem/orquestrador, os desafios opcionais.
