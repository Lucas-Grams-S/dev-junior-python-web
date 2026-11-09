# Cheatsheet: Docker e Compose

## Containers "soltos" do curso (módulos 3 e 7)
```bash
docker run --name minishop-pg -e POSTGRES_PASSWORD=dev -p 127.0.0.1:5432:5432 -v minishop_pgdata:/var/lib/postgresql -d postgres:18
docker run --name minishop-redis -p 127.0.0.1:6379:6379 -d redis:8
docker exec -it minishop-pg psql -U postgres -d loja            # shell do psql
docker exec -i minishop-pg psql -U postgres -d loja < arquivo.sql
docker volume rm minishop_pgdata                                 # apaga os dados!
```
⚠️ **Estes nomes (`minishop-pg`, `minishop_pgdata`) são seus.** Um projeto do Compose chamado `minishop` com um volume `pgdata` colidiria com eles (aula 11.04): dê ao projeto um `name:` único.

## Imagens e containers
```bash
docker run --rm IMAGEM CMD                    # roda e apaga ao terminar
docker run -d --name NOME -p 127.0.0.1:H:C IMAGEM   # segundo plano, porta só no host local
docker ps [-a] · docker logs [-f] [--since 30s] [-t] NOME · docker exec -it NOME sh
docker stop|start|restart NOME · docker rm [-f] NOME · docker top NOME · docker diff NOME
docker images · docker history IMAGEM · docker rmi IMAGEM · docker pull IMAGEM:TAG
docker inspect -f '{{.State.ExitCode}} {{.State.OOMKilled}} {{.RestartCount}}' NOME
docker stats --no-stream · docker cp NOME:/caminho ./destino
docker run --rm -it --entrypoint sh IMAGEM    # entra na imagem sem executar o CMD
```
**Antes de criar nomes:** `docker ps -a`, `docker volume ls`, `docker network ls`.

## Build
```bash
docker build -t nome:tag .                    # usa ./Dockerfile e o contexto "."
docker build --check .                        # avisos do Dockerfile (JSONArgsRecommended etc.)
docker build -f outro/Dockerfile -t nome:tag .
docker build --no-cache .                     # ignora o cache
```
Ordem do Dockerfile: base → dependências (`pyproject.toml` + `uv.lock`) → código → comandos de build → usuário. `CMD` sempre em **forma exec** (`["gunicorn", …]`). `USER` não root com UID fixo. `.dockerignore`: `.git`, `.venv`, `.env`, `*.sqlite3`.

## Compose
```bash
docker compose up -d [--build] [--wait]       # cria/atualiza e inicia
docker compose ps [-a] · logs [-f] [serv] · top [serv] · config [--volumes]
docker compose exec serv CMD                  # container em execução
docker compose run --rm [-e VAR=1] serv CMD   # container novo e descartável
docker compose stop|start|restart [serv]
docker compose down                           # remove containers e redes (MANTÉM volumes)
docker compose down -v                        # também apaga os volumes DO PROJETO (dados!)
docker compose up -d --scale worker=3
docker compose -f compose.yaml -f compose.dev.yaml up    # base + override
```
Esqueleto: `name:` **único** · `services` (`image`/`build`, `env_file`, `environment`, `ports`, `expose`, `volumes`, `networks`, `healthcheck`, `depends_on` com `condition`, `restart`) · `networks` · `volumes` · `secrets`.
`depends_on`: `service_started` · `service_healthy` · `service_completed_successfully`.

## Volumes, redes e segredos
```bash
docker volume ls · docker volume inspect V · docker volume rm V           # rm APAGA os dados
docker run --rm -v VOL:/v:ro -v "$PWD":/b alpine tar czf /b/VOL.tgz -C /v .   # backup de um volume
docker network ls · docker network inspect REDE
```
Tipos: volume **nomeado** (dados), **bind mount** (código em dev), `tmpfs`. Volume novo herda dono/permissões da pasta da imagem. PostgreSQL 18: montar em `/var/lib/postgresql`. Segredos: `secrets:` + `NOME_FILE`; `ARG`/`ENV` e `docker inspect` **expõem**.

## Códigos de saída
`0` ok · `1` erro do programa · `137` SIGKILL (stop estourado, `kill` ou OOM: veja `OOMKilled`) · `139` falha de segmentação · `143` SIGTERM.

## Gunicorn / Uvicorn / Nginx
```bash
gunicorn config.wsgi:application -b 0.0.0.0:8000 --workers 3 --timeout 30 --graceful-timeout 30 --access-logfile -
gunicorn ... --worker-class gthread --threads 8        # I/O com threads
uvicorn config.asgi:application --host 0.0.0.0 --port 8000 --workers 2 --proxy-headers --forwarded-allow-ips "*"
docker kill -s HUP NOME                                # recarrega os workers sem derrubar o servidor
docker compose exec nginx nginx -t                     # valida a configuração
```
Nginx → Django: `proxy_set_header Host $http_host; X-Forwarded-For $proxy_add_x_forwarded_for; X-Forwarded-Proto $scheme;` · WebSocket: `proxy_http_version 1.1; Upgrade $http_upgrade; Connection "upgrade";` · `client_max_body_size` · `log_format` **sem query string**. Django: `SECURE_PROXY_SSL_HEADER`, `NUM_PROXIES`, `ALLOWED_HOSTS`. Sinais: `502` upstream respondeu mal/recusou, `504` não respondeu a tempo.

## Diagnóstico (nesta ordem)
`docker compose ps -a` → `logs` → `inspect` → `exec`/`run`. "Up" **não** significa funcionando: use `healthcheck`.

## GitHub Actions (resumo do módulo 12)
```yaml
on: { pull_request: {}, push: { branches: [main] } }
permissions: { contents: read }
concurrency: { group: ci-${{ github.workflow }}-${{ github.ref }}, cancel-in-progress: true }
jobs:
  test:
    runs-on: ubuntu-24.04
    needs: [lint]                      # ordem entre jobs
    strategy: { fail-fast: false, matrix: { db: [sqlite, postgres] } }
    services: { postgres: { image: postgres:18, options: --health-cmd "pg_isready" } }
    steps: [ { uses: actions/checkout@<SHA> }, { run: uv run pytest -q } ]
```
Validar: `docker run --rm -v "$PWD":/repo -w /repo rhysd/actionlint:latest` (dentro de um repositório Git). Reproduzir: `git clone` + container limpo. Fixar actions por SHA (`gh api repos/<acao>/commits/<tag> --jq .sha`). Ambientes, branch protegida e revisores ficam **fora do YAML**.
