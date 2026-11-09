# Módulo 15 — FastAPI (comparativo)

> ⏱️ 7 sessões · 10.5 h · Pré-requisitos: Módulo 14 concluído (checkpoint aprovado).
> 🏷️ Marco no Git: `v4.2-fastapi`

## 🎯 Objetivos
- Implementar parte da API do MiniShop em FastAPI + SQLAlchemy + Pydantic
- Comparar tipagem, validação, async e injeção de dependências com Django/DRF
- Decidir quando escolher cada framework (incluindo Flask)

## 📖 Aulas

| # | Aula | Tempo |
|---|------|-------|
| 01 | [FastAPI e Pydantic](01-fastapi-pydantic.md) | 1h30 |
| 02 | [SQLAlchemy e Alembic](02-sqlalchemy-alembic.md) | 1h30 |
| 03 | [Async nativo, injeção de dependências e docs automática](03-async-dependencias-docs.md) | 1h30 |
| 04 | [FastAPI: testes e chamadas async com `httpx`](04-fastapi-async-httpx-testes.md) | 1h30 |
| 05 | [FastAPI: endpoints do catálogo do MiniShop](05-fastapi-endpoints-catalogo.md) | 1h30 |
| 06 | [Comparativo e “quando escolher cada um”](06-comparativo-quando-escolher.md) | 1h30 |
| 07 | [Checkpoint](checkpoint.md) (quiz de 10 questões, entrega prática, autoavaliação) | 1h30 |

> Se uma aula pedir mais de uma sessão, ela é dividida em parte 1 e parte 2 na geração do módulo.

## 📦 Entrega do projeto
Serviço `catalog-fastapi/` com `GET/POST /products` equivalente ao do DRF e tabela comparativa em [`comparativo.md`](comparativo.md).

## 🔗 Conexão com o próximo módulo
Próximo: [Módulo 16 — Pronto para o mercado](../16-pronto-para-o-mercado/README.md).

> ✅ Status: as 6 aulas e o checkpoint estão gerados. **Executado** com FastAPI 0.162.2, SQLAlchemy 2.1.8, Alembic 1.20.1, Pydantic 2.14.3, SQLite e PostgreSQL 18.6 (**30 testes** nos dois), comparação contra o Django do módulo 14 (13 iguais, 3 diferentes) e medição de carga. **Sem** `PATCH`/imagem/cache/JWT/Docker no FastAPI (é uma fatia). Referência em [`projeto/referencia-api-m15/catalog-fastapi/`](../projeto/referencia-api-m15/catalog-fastapi/README.md). Links conferidos com HTTP 200 em 2026-11-09.
