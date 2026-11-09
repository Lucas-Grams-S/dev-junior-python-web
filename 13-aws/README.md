# Módulo 13 — Introdução à nuvem com AWS

> ⏱️ 9 sessões · 13.5 h · Pré-requisitos: Módulo 12 concluído (checkpoint aprovado).
> 🏷️ Marco no Git: `v4.0-aws`

> 💸 **Atenção:** este módulo trata de serviços que **cobram**. Faça o orçamento e o MFA (aula 01) antes de tudo, use o simulador (`moto`) para praticar sem custo, e **destrua tudo no mesmo dia** (aula 08).

## 🎯 Objetivos
- Configurar conta com MFA e alerta de custos antes de qualquer recurso
- Aplicar IAM com menor privilégio
- Provisionar EC2, RDS e S3 dentro do que o plano gratuito cobre
- Fazer o deploy do MiniShop e acompanhar logs no CloudWatch
- Destruir tudo ao final e conferir que não há cobrança

## 📖 Aulas

| # | Aula | Tempo |
|---|------|-------|
| 01 | [Conceitos de nuvem, conta, MFA e alerta de custos](01-conceitos-conta-mfa-custos.md) | 1h30 |
| 02 | [Equivalências AWS ↔ Azure ↔ GCP (conceito, sem prática)](02-equivalencias-nuvens.md) | 1h30 |
| 03 | [IAM: usuários, papéis e políticas](03-iam.md) | 1h30 |
| 04 | [EC2, Security Groups e noção de VPC](04-ec2-security-groups-vpc.md) | 1h30 |
| 05 | [RDS (PostgreSQL gerenciado)](05-rds-postgres.md) | 1h30 |
| 06 | [S3 para arquivos de mídia](06-s3-midia.md) | 1h30 |
| 07 | [Deploy do MiniShop](07-deploy-minishop.md) | 1h30 |
| 08 | [Segredos, CloudWatch e como destruir tudo](08-segredos-cloudwatch-destruicao.md) | 1h30 |
| 09 | [Checkpoint](checkpoint.md) (quiz de 10 questões, entrega prática, autoavaliação) | 1h30 |

> Se uma aula pedir mais de uma sessão, ela é dividida em parte 1 e parte 2 na geração do módulo.

## 📦 Entrega do projeto
MiniShop no ar na AWS (URL pública), mídia no S3, banco no RDS — e um **roteiro de destruição** executado e conferido.

## 🔗 Conexão com o próximo módulo
Próximo: [Módulo 14 — Produção e observabilidade básica](../14-producao-observabilidade/README.md).

> ✅ Status: as 8 aulas e o checkpoint estão gerados. **Sem conta AWS no laboratório:** os scripts foram executados contra o simulador `moto` e o pacote de deploy num Compose local; **nada foi criado na AWS real**, então o marco `v4.0-aws` (URL pública e destruição conferida) só se cumpre por inteiro se você executar os scripts na sua conta (💸). Referência em [`projeto/referencia-api-m13/`](../projeto/referencia-api-m13/README.md). Links conferidos com HTTP 200 em 2026-11-09. **Leia a aula 01 antes de qualquer coisa.**
