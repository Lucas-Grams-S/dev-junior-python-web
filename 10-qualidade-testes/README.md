# Módulo 10 — Qualidade, testes e boas práticas

> ⏱️ 8 sessões · 12 h · Pré-requisitos: Módulo 9 concluído (checkpoint aprovado).
> 🏷️ Marco no Git: `v2.4-qualidade`

## 🎯 Objetivos
- Estruturar a pirâmide de testes do MiniShop com pytest
- Usar fixtures, parametrize e mocks
- Configurar ruff, mypy e pre-commit
- Dar e receber code review; escrever Conventional Commits e um bom README
- Trabalhar em time ágil e usar IA de forma responsável

## 📖 Aulas

| # | Aula | Tempo |
|---|------|-------|
| 01 | [Pirâmide de testes e fixtures](01-piramide-fixtures.md) | 1h30 |
| 02 | [`parametrize` e mocks](02-parametrize-mocks.md) | 1h30 |
| 03 | [Testes de integração, de API e cobertura](03-integracao-api-cobertura.md) | 1h30 |
| 04 | [TDD (introdução)](04-tdd.md) | 1h30 |
| 05 | [ruff, mypy e pre-commit](05-ruff-mypy-precommit.md) | 1h30 |
| 06 | [Code review, Conventional Commits e README](06-code-review-commits-readme.md) | 1h30 |
| 07 | [Metodologias ágeis, trabalho em time e IA assistida](07-agil-ia-assistida.md) | 1h30 |
| 08 | [Checkpoint](checkpoint.md) (quiz de 10 questões, entrega prática, autoavaliação) | 1h30 |

> Se uma aula pedir mais de uma sessão, ela é dividida em parte 1 e parte 2 na geração do módulo.

## 📦 Entrega do projeto
Cobertura ≥ 80% nas camadas de negócio, `pre-commit` ativo, README profissional e histórico com Conventional Commits.

## 🔗 Conexão com o próximo módulo
Próximo: [Módulo 11 — Docker e containers](../11-docker/README.md).

> ✅ Status: as 7 aulas e o checkpoint estão gerados. **Todo o código foi executado** num laboratório (Python 3.13, Django 5.2.19; `pytest`, `ruff`, `mypy`, `pre-commit`, `commitizen`; 302 testes), reproduzido em [`projeto/referencia-api-m10/`](../projeto/referencia-api-m10/README.md). Links de “Para ir além” conferidos com HTTP 200 em 2026-11-08. Não executado: CI de verdade (módulo 12), `mutmut`, `hypothesis`, pessoas reais em programação em par/Scrum e os desafios opcionais.
