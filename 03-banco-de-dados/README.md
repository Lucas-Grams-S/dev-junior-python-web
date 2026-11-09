# Módulo 3 — Bancos de dados relacionais

> ⏱️ 13 sessões · 19.5 h · Pré-requisitos: Módulo 2 concluído (checkpoint aprovado).
> 🏷️ Marco no Git: `v0.3-banco-sql`

## 🎯 Objetivos
- Modelar entidades e relacionamentos (ER) e normalizar até a 3FN
- Escrever SQL: DDL, DML, JOINs, agregações e subqueries
- Criar constraints e índices e ler um `EXPLAIN`
- Explicar transações e ACID com um exemplo de transferência
- Acessar o PostgreSQL via `psycopg` evitando SQL injection

## 📖 Aulas

| # | Aula | Tempo |
|---|------|-------|
| 01 | [Por que usar banco; modelagem e diagrama ER](01-por-que-banco-modelagem-er.md) | 1h30 |
| 02 | [Normalização (1FN a 3FN) e quando desnormalizar](02-normalizacao.md) | 1h30 |
| 03 | [PostgreSQL com Docker, DDL e DML](03-postgres-docker-ddl-dml.md) | 1h30 |
| 04 | [SELECT, WHERE, ORDER BY e LIMIT](04-select-where-order-limit.md) | 1h30 |
| 05 | [JOINs](05-joins.md) | 1h30 |
| 06 | [GROUP BY, HAVING e subqueries](06-group-by-subqueries.md) | 1h30 |
| 07 | [SQL na prática: lista de exercícios com as consultas da loja](07-sql-pratica-exercicios.md) | 1h30 |
| 08 | [Constraints, índices e `EXPLAIN`](08-constraints-indices-explain.md) | 1h30 |
| 09 | [Transações, ACID e níveis de isolamento](09-transacoes-acid.md) | 1h30 |
| 10 | [Python + PostgreSQL com `psycopg` e SQL injection](10-psycopg-sql-injection.md) | 1h30 |
| 11 | [ORM, migrações e noção de NoSQL (Redis, MongoDB)](11-orm-migracoes-nosql.md) | 1h30 |
| 12 | [Mini-projeto: banco da loja em SQL puro](12-projeto-banco-da-loja.md) | 1h30 |
| 13 | [Checkpoint](checkpoint.md) (quiz de 10 questões, entrega prática, autoavaliação) | 1h30 |

> Se uma aula pedir mais de uma sessão, ela é dividida em parte 1 e parte 2 na geração do módulo.

## 📦 Entrega do projeto
**Banco da loja em SQL puro** (schema, seed, consultas de relatório, índices) em `projeto/sql/`, base do schema do MiniShop.

## 🔗 Conexão com o próximo módulo
Próximo: [Módulo 4 — Front-end essencial para dev backend](../04-front-end-essencial/README.md).

> ✅ Status: conteúdo gerado; todo o SQL e o Python foram executados em PostgreSQL 18.6 (Docker) em 2026-11-07. MongoDB e a interface gráfica de ferramentas não foram executados (marcado nas aulas).
