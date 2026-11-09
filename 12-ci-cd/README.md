# Módulo 12 — CI/CD

> ⏱️ 3 sessões · 4.5 h · Pré-requisitos: Módulo 11 concluído (checkpoint aprovado).
> 🏷️ Marco no Git: `v3.1-ci`

## 🎯 Objetivos
- Explicar integração e entrega contínuas
- Criar um workflow do GitHub Actions com lint, testes e build da imagem
- Distinguir ambientes dev/staging/produção e estratégias de deploy simples

## 📖 Aulas

| # | Aula | Tempo |
|---|------|-------|
| 01 | [CI/CD e GitHub Actions](01-conceitos-github-actions.md) | 1h30 |
| 02 | [Pipeline completo: lint, testes, build e ambientes](02-pipeline-completo.md) | 1h30 |
| 03 | [Checkpoint](checkpoint.md) (quiz de 10 questões, entrega prática, autoavaliação) | 1h30 |

> Se uma aula pedir mais de uma sessão, ela é dividida em parte 1 e parte 2 na geração do módulo.

## 📦 Entrega do projeto
Pipeline `.github/workflows/ci.yml` verde em todo PR, com build da imagem e badge no README.

## 🔗 Conexão com o próximo módulo
Próximo: [Módulo 13 — Introdução à nuvem com AWS](../13-aws/README.md).

> ✅ Status: as 2 aulas e o checkpoint estão gerados. **Executado no GitHub de verdade** (repositório privado): CI verde em ≈ 2,5 min; o primeiro push reprovou por dois defeitos reais (corrigidos); a produção rodou sem aprovação porque o plano gratuito não oferece revisores de `environment` nem proteção de branch em repositório privado. Referência em [`projeto/referencia-api-m12/`](../projeto/referencia-api-m12/README.md). Links conferidos com HTTP 200 em 2026-11-08.
