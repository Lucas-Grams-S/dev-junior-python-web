# Módulo 6 — APIs REST

> ⏱️ 15 sessões · 22.5 h · Pré-requisitos: Módulo 5 concluído (checkpoint aprovado).
> 🏷️ Marco no Git: `v2.0-minishop-api`

## 🎯 Objetivos
- Aplicar princípios REST, idempotência e statelessness no desenho de endpoints
- Implementar serializers, viewsets e routers com DRF
- Proteger a API (token/JWT, permissões, throttling)
- Documentar com OpenAPI/Swagger e configurar CORS
- Testar a API de ponta a ponta

## 📖 Aulas

| # | Aula | Tempo |
|---|------|-------|
| 01 | [Princípios REST](01-principios-rest.md) | 1h30 |
| 02 | [Design de endpoints e convenções](02-design-endpoints.md) | 1h30 |
| 03 | [DRF: serializers](03-drf-serializers.md) | 1h30 |
| 04 | [DRF: views, viewsets e routers](04-drf-views-viewsets-routers.md) | 1h30 |
| 05 | [Validação e tratamento de erros padronizado](05-validacao-erros.md) | 1h30 |
| 06 | [Autenticação por token/JWT](06-autenticacao-token-jwt.md) | 1h30 |
| 07 | [Permissões](07-drf-permissoes.md) | 1h30 |
| 08 | [Filtros, busca e ordenação](08-filtros-busca-ordenacao.md) | 1h30 |
| 09 | [Paginação e throttling](09-paginacao-throttling.md) | 1h30 |
| 10 | [Versionamento e documentação OpenAPI/Swagger](10-versionamento-openapi.md) | 1h30 |
| 11 | [CORS](11-cors.md) | 1h30 |
| 12 | [Testes de API](12-testes-de-api.md) | 1h30 |
| 13 | [GraphQL e gRPC (conceito) e fechamento da API do MiniShop](13-graphql-grpc-api-completa.md) | 1h30 |
| 14 | [Front-end simples consumindo a API do MiniShop](14-front-consome-api.md) | 1h30 |
| 15 | [Checkpoint](checkpoint.md) (quiz de 10 questões, entrega prática, autoavaliação) | 1h30 |

> Se uma aula pedir mais de uma sessão, ela é dividida em parte 1 e parte 2 na geração do módulo.

## 📦 Entrega do projeto
**API REST do MiniShop** documentada em `/api/docs/`, com autenticação JWT, filtros, paginação, throttling, testes e um front-end simples consumindo-a.

## 🔗 Conexão com o próximo módulo
Próximo: [Módulo 7 — Comunicação síncrona e assíncrona](../07-sincrono-assincrono/README.md).

> ✅ Status: as 14 aulas e o checkpoint estão gerados. **Todo o código das aulas foi executado** num laboratório (Django 5.2.19, DRF 3.18.3; 65 testes, 93% de cobertura, 12 testes Node e 15 verificações E2E no Chrome 156), reproduzido em [`projeto/referencia-api-m6/`](../projeto/referencia-api-m6/README.md). Links de “Para ir além” conferidos com HTTP 200 em 2026-11-08. Não executado: o trecho ilustrativo de `v2` da aula 10 e os desafios opcionais; o banco do laboratório é SQLite (concorrência real e `ILIKE` pedem PostgreSQL).
