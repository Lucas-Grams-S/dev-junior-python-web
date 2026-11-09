# Módulo 8 — Estrutura de projetos e arquitetura

> ⏱️ 8 sessões · 12 h · Pré-requisitos: Módulo 7 concluído (checkpoint aprovado).
> 🏷️ Marco no Git: `v2.2-arquitetura-camadas`

## 🎯 Objetivos
- Separar responsabilidades em views, services e repositories
- Aplicar SOLID, DRY, KISS e YAGNI sem exagero
- Usar Strategy, Factory, Repository e Adapter onde fazem sentido
- Comparar monólito, monólito modular e microsserviços
- Refatorar código legado com segurança (testes primeiro)

## 📖 Aulas

| # | Aula | Tempo |
|---|------|-------|
| 01 | [Organização de código e arquitetura em camadas](01-responsabilidades-camadas.md) | 1h30 |
| 02 | [Services e repositories no MiniShop](02-services-repositories.md) | 1h30 |
| 03 | [SOLID, DRY, KISS e YAGNI em Python](03-solid-dry-kiss-yagni.md) | 1h30 |
| 04 | [Strategy, Factory, Repository e Adapter](04-padroes-de-projeto.md) | 1h30 |
| 05 | [Monólito vs monólito modular vs microsserviços](05-monolito-vs-microsservicos.md) | 1h30 |
| 06 | [Twelve-factor app](06-twelve-factor.md) | 1h30 |
| 07 | [Leitura de código legado e refatoração segura](07-legado-refatoracao.md) | 1h30 |
| 08 | [Checkpoint](checkpoint.md) (quiz de 10 questões, entrega prática, autoavaliação) | 1h30 |

> Se uma aula pedir mais de uma sessão, ela é dividida em parte 1 e parte 2 na geração do módulo.

## 📦 Entrega do projeto
MiniShop refatorado em camadas (`services/`, `repositories/`), Adapter para o gateway de pagamento e ADRs curtos em `docs/adr/`.

## 🔗 Conexão com o próximo módulo
Próximo: [Módulo 9 — Segurança](../09-seguranca/README.md).

> ✅ Status: as 7 aulas e o checkpoint estão gerados. **Todo o código foi executado** num laboratório (Python 3.13, Django 5.2.19; Gunicorn, servidor de pagamento simulado, PostgreSQL 18.6 em contêiner; 147 testes; 3 contratos de arquitetura), reproduzido em [`projeto/referencia-api-m8/`](../projeto/referencia-api-m8/README.md). Links de “Para ir além” conferidos com HTTP 200 em 2026-11-08. Não executado: provedor de pagamento real, microsserviços de verdade, nuvem/orquestrador e os desafios opcionais.
