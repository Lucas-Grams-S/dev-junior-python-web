# Módulo 11 — Docker e containers

> ⏱️ 7 sessões · 10.5 h · Pré-requisitos: Módulo 10 concluído (checkpoint aprovado).
> 🏷️ Marco no Git: `v3.0-docker`

> ⚠️ **Antes de começar:** rode `docker ps -a` e `docker volume ls`. Se você já tem o `minishop-pg`/`minishop_pgdata` do módulo 3, **não** dê ao projeto do Compose o nome `minishop` (veja a aula 04).

## 🎯 Objetivos
- Explicar imagem vs container e escrever um Dockerfile eficiente e seguro
- Orquestrar app + PostgreSQL + Redis + worker com Compose
- Depurar via logs e `exec` dentro do container
- Entender Gunicorn/Uvicorn atrás de Nginx

## 📖 Aulas

| # | Aula | Tempo |
|---|------|-------|
| 01 | [O problema que o Docker resolve](01-problema-docker.md) | 1h30 |
| 02 | [Dockerfile para Django (camadas, slim, não root)](02-dockerfile-django.md) | 1h30 |
| 03 | [Docker Compose: app + PostgreSQL + Redis + worker](03-docker-compose.md) | 1h30 |
| 04 | [Volumes, redes e variáveis de ambiente](04-volumes-redes-env.md) | 1h30 |
| 05 | [Logs, depuração e `.dockerignore`](05-logs-debug-dockerignore.md) | 1h30 |
| 06 | [Gunicorn/Uvicorn atrás de Nginx](06-gunicorn-nginx.md) | 1h30 |
| 07 | [Checkpoint](checkpoint.md) (quiz de 10 questões, entrega prática, autoavaliação) | 1h30 |

> Se uma aula pedir mais de uma sessão, ela é dividida em parte 1 e parte 2 na geração do módulo.

## 📦 Entrega do projeto
`docker compose up` sobe o MiniShop completo (web, db, redis, worker) com um comando.

## 🔗 Conexão com o próximo módulo
Próximo: [Módulo 12 — CI/CD](../12-ci-cd/README.md).

> ✅ Status: as 6 aulas e o checkpoint estão gerados. **Todo o código foi executado** num laboratório (Docker 29.9.2, Compose v5.6.1; `python:3.13-slim`, `postgres:18`, `redis:8`, `nginx:1.29-alpine`; 302 testes do projeto continuam verdes), reproduzido em [`projeto/referencia-api-m11/`](../projeto/referencia-api-m11/README.md). Links de “Para ir além” conferidos com HTTP 200 em 2026-11-08. A aula 04 registra um **erro real de laboratório** (colisão de nome de volume). Não executado: certificados reais, várias réplicas do `web`, `hadolint`, `uvicorn-worker` e os desafios opcionais.
