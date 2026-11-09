# Mapa do módulo 11 (material do curso)

Este diretório é o **laboratório usado para executar e verificar** as aulas do módulo 11: o projeto do módulo 10 (302 testes) com a camada de **containers** por cima. O `README.md` é o do próprio MiniShop (agora com a seção "Rodando com Docker").

| Onde | Aula |
|---|---|
| `docker-lab/Dockerfile.ingenuo` (o ponto de partida ruim), `Dockerfile` (multi-stage, `uv`, usuário `app`), `config/settings.py` (`STATIC_ROOT`) | 11.02 |
| `compose.yaml` (`db`, `redis`, `migrate`, `web`, `worker`), `.env.docker.example`, `docker-lab/compose.sem-espera.yaml` (a corrida sem `healthcheck`) | 11.03 |
| `compose.yaml` (volumes e redes), `compose.dev.yaml` (bind mount e recarga), `config/envconf.py` (`env_or_file`), `docker-lab/compose.segredos.yaml` | 11.04 |
| `.dockerignore`, `docker-lab/Dockerfile.copia-tudo`, `config/healthcheck.py` | 11.05 |
| `nginx/` (`Dockerfile`, `nginx.conf`), `compose.asgi.yaml`, `scripts/smoke_docker.sh` | 11.06 |

A aula 11.01 só usa imagens públicas (`alpine`, `python:3.13-slim`).

**Verificação rápida** (precisa só do Docker): `cp .env.docker.example .env && bash scripts/smoke_docker.sh`.

**Cuidado com nomes.** O projeto do Compose chama-se `minishop-docker` **de propósito**: com o nome `minishop`, o volume `pgdata` viraria `minishop_pgdata`, o mesmo nome do volume do PostgreSQL do módulo 3 (veja a aula 11.04).
