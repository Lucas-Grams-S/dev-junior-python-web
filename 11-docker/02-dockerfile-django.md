# 2. Dockerfile para Django (camadas, cache, imagem slim, usuário não root)

> ⏱️ ~1h30 · Módulo 11 · Pré-requisitos: [11.01](01-problema-docker.md), [Módulo 8 (configuração por ambiente)](../08-arquitetura/README.md), [9.06 (segredos)](../09-seguranca/06-segredos-dependencias-headers-rate-limit.md)

> ✅ **Verificação.** Tudo executado em 2026-11-08 sobre o MiniShop do módulo 10 (302 testes), com Docker 29.9.2, `python:3.13-slim` (Python 3.13.18) e `uv` 0.9. **As saídas e os tempos são reais** (máquina de desenvolvimento comum, rede rápida; os seus números serão diferentes, a **proporção** não). O código está em [`projeto/referencia-api-m11/`](../projeto/referencia-api-m11/README.md).

## 🎯 Objetivos
- Escrever um **Dockerfile** para o MiniShop e explicar cada instrução
- Ordenar as instruções para **aproveitar o cache de camadas** (e medir o ganho)
- Usar **imagem `slim`** e **multi-stage** para reduzir o tamanho
- Rodar a aplicação como **usuário não root** e provar que funciona
- Escolher entre **forma exec e forma shell** de `CMD` e mostrar a consequência no `docker stop`

## 🤔 Por que isso importa
O Dockerfile é o **contrato** entre o seu código e o servidor: tudo o que a aplicação precisa para rodar está escrito ali. Um Dockerfile ruim produz imagens gigantes (lentas para enviar e baixar), reconstruções de minutos a cada vírgula alterada, aplicações rodando como `root` e containers que demoram 10 s para parar. Em time, é você quem vai ajustar o Dockerfile quando o build do CI ficar lento ou quando a segurança pedir "tire o root".

## 💡 Intuição (explicação simples)
Montar uma imagem é como **empilhar caixas numa ordem fixa**: se você troca o conteúdo de uma caixa no meio da pilha, precisa **refazer essa caixa e todas as de cima**. Logo, coloque embaixo o que quase nunca muda (o sistema, as dependências) e em cima o que muda toda hora (o seu código). E há ainda a **mala de viagem**: você usa uma oficina cheia de ferramentas (compiladores, caches) para montar a peça, mas leva para a viagem **só a peça pronta**. É o multi-stage.

## 🔬 Como funciona por dentro
- **Cada instrução** (`FROM`, `RUN`, `COPY`, …) cria uma camada. O Docker guarda o resultado em **cache** com uma chave: *a instrução + o conteúdo dos arquivos que ela usa + a camada anterior*. Se a chave não mudou, reaproveita; se mudou, **refaz essa e todas as seguintes**.
  ```mermaid
  flowchart TB
      A[FROM python:3.13-slim] --> B[instala dependências<br/>muda pouco: pyproject.toml + uv.lock]
      B --> C[COPY código<br/>muda a cada commit]
      C --> D[collectstatic]
      style B fill:#cfe8cf
      style C fill:#f5d5d5
  ```
- **Contexto de build.** `docker build .` envia a pasta `.` (o *contexto*) ao Docker; só o que está nele pode ser copiado. A aula 05 mostra como o `.dockerignore` controla isso. Aqui copiamos **pastas específicas**.
- **Imagens-base.** `python:3.13` (Debian completa, ~1 GB) × `python:3.13-slim` (Debian enxuta, 178 MB) × `python:3.13-alpine` (musl libc; menor, mas várias bibliotecas com extensões em C, como `psycopg` e `grpcio`, precisam compilar ou não têm *wheel* pronta: mais trabalho, **não** recomendado para quem começa). Use **`slim`**.
- **Multi-stage.** Vários `FROM` no mesmo arquivo; cada um é uma etapa. A imagem final é a **última**, e ela busca só o que quiser das anteriores com `COPY --from=<etapa>`. Compiladores, caches e arquivos temporários da etapa de construção ficam para trás.
- **`uv` no Docker.** Três detalhes: (1) `uv sync --frozen --no-dev --no-install-project` instala **exatamente** o `uv.lock` (sem resolver de novo), **sem** as dependências de desenvolvimento e **sem** instalar o projeto (que ainda não foi copiado: é o que mantém essa camada em cache); (2) `--mount=type=cache` guarda o cache de downloads do `uv` **fora da imagem**, entre builds; (3) `--mount=type=bind` usa `pyproject.toml` e `uv.lock` sem criar camada com eles.
- **Usuário não root.** Por padrão o processo do container é `root` (UID 0). Se alguém explorar uma falha da aplicação, ganha root **dentro** do container, e com um kernel compartilhado isso é um passo perigoso (aula 01). Crie um usuário de sistema com **UID fixo** (previsível para volumes e para plataformas como Kubernetes) e use `USER`.
- **`CMD` em forma exec × shell.** `CMD ["gunicorn", "..."]` (lista JSON) executa o programa **diretamente**: ele é o PID 1 e recebe o `SIGTERM` do `docker stop`. `CMD gunicorn ...` (texto) roda `/bin/sh -c "gunicorn ..."`: o PID 1 é o **shell**, que não repassa o sinal. O Docker espera 10 s e então mata à força (`SIGKILL`, código 137).
- **`EXPOSE`** só documenta a porta; não publica nada. **`ENV PYTHONUNBUFFERED=1`** faz o Python escrever os logs na hora (a aula 05 mostra a diferença) e **`PYTHONDONTWRITEBYTECODE=1`** evita `.pyc` soltos.

## 🛠️ Exemplo prático
A pasta de trabalho é a do MiniShop (`projeto/referencia-api-m11/`).

**1. O Dockerfile ingênuo (para medir o que NÃO fazer).** `docker-lab/Dockerfile.ingenuo`:
```dockerfile
FROM python:3.13
WORKDIR /app
COPY . .
RUN pip install uv && uv sync
CMD python manage.py runserver 0.0.0.0:8000
```
```bash
time docker build -f docker-lab/Dockerfile.ingenuo -t minishop:ingenuo .
docker images minishop:ingenuo --format '{{.Repository}}:{{.Tag}} {{.Size}}'
docker run --rm minishop:ingenuo id
```
```text
real	0m44.416s
minishop:ingenuo 2.17GB
uid=0(root) gid=0(root) groups=0(root)
```
**2,17 GB, 44 s e root.** Agora, o teste que dói: mude **uma linha** de código e reconstrua.
```bash
echo "# editei uma linha" >> apps/catalog/models.py
time docker build -f docker-lab/Dockerfile.ingenuo -t minishop:ingenuo .
```
```text
#7 [3/4] COPY . .                 ← mudou: refaz
#8 [4/4] RUN pip install uv && uv sync
#8 DONE 7.8s                      ← e reinstala TODAS as dependências
real	0m21.888s
```
Porque `COPY . .` vem **antes** da instalação, qualquer alteração de código invalida a camada das dependências. (Reverta a linha com um editor.) O próprio Docker avisa do `CMD`: `docker build --check -f docker-lab/Dockerfile.ingenuo .` imprime `WARNING: JSONArgsRecommended … JSON arguments recommended for CMD to prevent unintended behavior related to OS signals`.

**2. O Dockerfile do MiniShop** (`Dockerfile`):
```dockerfile
# syntax=docker/dockerfile:1

# ---------- base: o que as duas etapas compartilham ----------
FROM python:3.13-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# ---------- builder: instala dependências (esta etapa NÃO vai para a imagem final) ----------
FROM base AS builder
COPY --from=ghcr.io/astral-sh/uv:0.9 /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never
WORKDIR /app

# 1) Dependências primeiro: só dependem de pyproject.toml e uv.lock, que mudam raramente.
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-dev --no-install-project

# 2) Código depois: muda a cada commit, então vem por último.
COPY manage.py ./
COPY config config
COPY apps apps
COPY legado legado

# 3) Arquivos estáticos (admin, DRF) são coletados na construção.
RUN SECRET_KEY=so-para-o-build /app/.venv/bin/python manage.py collectstatic --noinput

# ---------- runtime: a imagem que roda ----------
FROM base AS runtime
RUN groupadd --system --gid 10001 app \
 && useradd --system --uid 10001 --gid app --no-create-home --shell /usr/sbin/nologin app
WORKDIR /app
COPY --from=builder --chown=app:app /app /app
ENV PATH="/app/.venv/bin:$PATH"
USER app
EXPOSE 8000
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--access-logfile", "-"]
```
Dois acertos pequenos no projeto: `settings.py` ganhou `STATIC_ROOT = Path(os.environ.get("STATIC_ROOT", BASE_DIR / "staticfiles"))` (sem ele o `collectstatic` não sabe para onde copiar), e a chave `SECRET_KEY=so-para-o-build` existe **apenas naquele `RUN`** (variável de ambiente inline: não fica na imagem). `docker build --check .` responde `Check complete, no warnings found.`

**3. Construir e comparar.**
```bash
time docker build -t minishop:dev .
docker images --format '{{.Repository}}:{{.Tag}} {{.Size}}' | grep minishop
```
```text
real	0m15.592s
minishop:dev 452MB          (o Dockerfile ingênuo: 2.17GB)
```
De **2,17 GB para 452 MB (−79%)**. A base `slim` (178 MB) pesa muito menos que a completa (`python:3.13`, na casa de 1 GB, valor de referência que não medi aqui); o resto vem de não instalar as dependências de desenvolvimento (o `.venv` do Dockerfile ingênuo tinha 328 MB, o deste, 205 MB) e de não deixar caches. Onde estão os 452 MB?
```bash
docker run --rm minishop:dev sh -c 'du -sh /app/.venv /app/apps /app/staticfiles; du -sh /app/.venv/lib/python3.13/site-packages/* | sort -rh | head -4'
```
```text
205M	/app/.venv
752K	/app/apps
3.4M	/app/staticfiles
50M	django
19M	grpc
15M	pillow.libs
11M	psycopg_binary.libs
```
Seu código tem **752 KB**; as dependências, 205 MB. (`grpc` e `pillow` entraram nos módulos 6 e 7 como estudo; um projeto real separaria o que é só de laboratório, o que reduziria a imagem. Fica como exercício.)

**4. O cache em ação.** Reconstruir sem mudar nada, depois mudando só o código, depois mudando uma dependência:
```bash
docker build -t minishop:dev .                        # 1) nada mudou
echo "# editei" >> apps/catalog/models.py ; docker build -t minishop:dev .     # 2) uma linha de código
echo "# x" >> pyproject.toml ; docker build -t minishop:dev .                  # 3) o arquivo de dependências
```
| Situação | Etapas em cache | Etapas refeitas | Tempo |
|---|---|---|---|
| nada mudou | 11 | 0 | **1,3 s** |
| uma linha de código | 7 | 3 (`COPY` do código, `collectstatic`, cópia final) | **9,3 s** |
| `pyproject.toml` | 4 | 5 (reinstala as dependências) | 11,1 s |
Compare: o Dockerfile ingênuo gastou **21,9 s** na mesma mudança de código, e **reinstalou tudo**; o novo **não tocou nas dependências** (boa parte dos 9 s é copiar e exportar a camada de 219 MB da imagem final). Em disco, o cache do `uv` (`--mount=type=cache`) acelera até o caso 3, porque os pacotes já baixados não são baixados de novo.

**5. Não é root.**
```bash
docker run --rm minishop:dev id
docker run --rm minishop:dev sh -c 'touch /app/x; touch /etc/x'
```
```text
uid=10001(app) gid=10001(app) groups=10001(app)
touch: cannot touch '/app/x': Permission denied
touch: cannot touch '/etc/x': Permission denied
```
O processo não consegue escrever nem no próprio diretório da aplicação nem em `/etc`: um invasor teria muito menos o que fazer.

**6. Rodar.** (O Compose da aula 03 faz isto por você; aqui, à mão, para ver os erros.)
```bash
docker run -d --name teste-web -e SECRET_KEY=teste-local -p 127.0.0.1:8011:8000 minishop:dev
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8011/api/v1/products/
```
```text
400
```
**400 Bad Request.** A configuração segura do módulo 8 (`DEBUG=False` por padrão) **exige** `ALLOWED_HOSTS`; sem ele o Django recusa o cabeçalho `Host`. Corrigindo:
```bash
docker rm -f teste-web
docker run -d --name teste-web -e SECRET_KEY=teste-local -e SECURE_SSL_REDIRECT=0 -e ALLOWED_HOSTS=localhost,127.0.0.1 -p 127.0.0.1:8011:8000 minishop:dev
curl -s -w "\n-> %{http_code}\n" http://127.0.0.1:8011/api/v1/products/
docker logs teste-web 2>&1 | tail -3
```
```text
{"detail": "Erro interno. Tente novamente mais tarde.", "code": "server_error"}
-> 500
django.db.utils.OperationalError: unable to open database file
```
**500, e o log diz o motivo:** sem `DATABASE_URL`, o projeto cai no SQLite em `/app/db.sqlite3`, e o usuário `app` não pode criar arquivos em `/app` (acabamos de ver). **Isso é bom:** a aplicação não deveria gravar dados dentro do container. O banco será um PostgreSQL, em outro container, e é exatamente a aula 03. (`docker rm -f teste-web` para limpar.)

**7. `CMD` em forma exec × shell: o `docker stop`.** Construímos uma variante só trocando a forma do `CMD`:
```bash
printf 'FROM minishop:dev\nCMD gunicorn config.wsgi:application --bind 0.0.0.0:8000\n' | docker build -q -t minishop:forma-shell -f - .
docker run -d --name t-shell -e SECRET_KEY=x minishop:forma-shell ; sleep 2
docker top t-shell -o pid,cmd
time docker stop t-shell ; docker inspect -f 'exit={{.State.ExitCode}}' t-shell
```
```text
PID      CMD
1186237  /bin/sh -c gunicorn config.wsgi:application --bind 0.0.0.0:8000      ← PID 1 é o SHELL
1186275  /app/.venv/bin/python /app/.venv/bin/gunicorn config.wsgi:application ...
real	0m10.105s
exit=137
```
```bash
docker run -d --name t-exec -e SECRET_KEY=x minishop:dev ; sleep 2
time docker stop t-exec ; docker inspect -f 'exit={{.State.ExitCode}}' t-exec
```
```text
real	0m0.415s
exit=0
```
**10,1 s e código 137 (morto à força)** contra **0,4 s e código 0 (saída limpa)**. Em produção, uma parada suave deixa o Gunicorn terminar as requisições em andamento; a forma shell as derruba. Repare que **a mesma aplicação** só mudou na forma de uma linha.

## 🧠 Pausa para lógica
**Problema.** Um Dockerfile tem 5 camadas na ordem: (1) base, (2) `COPY` do código, (3) instalação das dependências, (4) `collectstatic`, (5) usuário. Quando você muda **um arquivo de código**, quais camadas são refeitas? Se a ordem fosse (1) base, (2) dependências, (3) código, (4) collectstatic, (5) usuário, e você mudasse um arquivo de código, quantas camadas seriam refeitas, e quantos segundos você economizaria sabendo que as dependências levam 7,8 s e o resto 1 s no total?

<details><summary>Dica</summary>Uma camada é refeita quando sua entrada muda <em>ou</em> quando qualquer camada anterior foi refeita.</details>

<details><summary>Solução comentada</summary>

Na primeira ordem, o código (camada 2) mudou, então **2, 3, 4 e 5** são refeitas, incluindo as dependências (camada 3): ≈ 7,8 + 1 = **8,8 s**. Na segunda, a camada 2 (dependências) fica em cache e só **3, 4 e 5** são refeitas: ≈ **1 s**. A economia é de **~7,8 s por build**, e se são 40 builds por dia na equipe (e no CI), o ganho passa de 5 minutos por dia. A regra: **o que muda menos, mais embaixo**.
</details>

## ⚠️ Erros comuns e boas práticas
| Sintoma / mensagem | Causa | Solução |
|---|---|---|
| Qualquer mudança reinstala tudo | `COPY . .` antes da instalação | Copiar `pyproject.toml`/`uv.lock` e instalar **antes** do código |
| `uv.lock` ausente ou antigo: `--frozen` falha | Esqueceu de commitar o lock | `uv lock` e versionar; o build deve falhar mesmo (reprodutibilidade) |
| `400 Bad Request` ao acessar | `ALLOWED_HOSTS` vazio com `DEBUG=0` | Definir `ALLOWED_HOSTS` |
| `django.core.exceptions.ImproperlyConfigured: SECRET_KEY é obrigatória` | `DEBUG=0` sem a variável | Passar `-e SECRET_KEY=…` (ou `env_file`, aula 04) |
| `unable to open database file` | SQLite em pasta não gravável | Usar PostgreSQL por `DATABASE_URL` (aula 03) |
| `docker stop` demora 10 s e dá 137 | `CMD` em forma shell (PID 1 = `sh`) | Forma exec, em lista JSON |
| `ModuleNotFoundError` só no container | Dependência não está no `pyproject.toml` (estava instalada à mão no seu ambiente) | Declarar no `pyproject` e regenerar o lock |
| `exec format error` | Imagem para outra arquitetura (construída num Mac com chip ARM, rodando em servidor x86) | `docker build --platform linux/amd64 …` |
| Segredo "para o build" aparece na imagem | `ARG`/`ENV` no Dockerfile ficam em `docker history` | Variável **inline** num único `RUN`; segredo de verdade via `--mount=type=secret` |
| Imagem enorme | Base completa, ferramentas de teste, caches | `slim`, multi-stage, `--no-dev`, `.dockerignore` (aula 05) |

- **Uma tag fixa e específica** (`python:3.13-slim`); para builds 100% reproduzíveis, fixe também o *digest* (`python:3.13-slim@sha256:…`) e deixe uma ferramenta (Dependabot, Renovate) atualizar.
- **Nada de segredos na imagem**: ela é distribuída e inspecionável (`docker history`, `docker inspect`).
- **Um Dockerfile, vários ambientes**: o que muda (chaves, endereços) entra por **variáveis de ambiente** na hora de rodar (aula 04), nunca no build.
- **Linters ajudam:** `docker build --check` (embutido, como visto) e o [hadolint](https://github.com/hadolint/hadolint) (não executado aqui).
- **Reduza o que roda como root.** `USER app` é a primeira defesa; a segunda é montar sistemas de arquivos somente leitura (`read_only: true`, tema de produção).

## 🧩 Exercícios
**1. Fixação.** (a) Por que `COPY . .` antes da instalação é um erro? (b) O que `--no-install-project` e `--frozen` fazem? (c) Para que serve o multi-stage? (d) Por que um UID fixo (10001) no usuário? (e) O que muda entre `CMD ["a"]` e `CMD a`?

<details><summary>Solução</summary>

(a) Qualquer alteração de código invalida a camada seguinte, que é a instalação das dependências. (b) `--no-install-project` instala só as dependências (o projeto ainda não foi copiado, mantendo a camada em cache); `--frozen` usa o `uv.lock` como está, sem resolver. (c) Ferramentas e caches de construção ficam fora da imagem final. (d) Volumes e plataformas (Kubernetes) tratam permissões por número; um UID previsível evita surpresas. (e) A lista executa o programa direto (PID 1, recebe sinais); o texto passa por `/bin/sh -c`.
</details>

**2. Aplicação no projeto MiniShop.**
- [ ] `Dockerfile` multi-stage com `python:3.13-slim`, `uv sync --frozen --no-dev`, `collectstatic`, `USER` não root (UID fixo) e `CMD` em forma exec
- [ ] `STATIC_ROOT` configurado; `docker build --check .` **sem avisos**
- [ ] Tabela no `docs/docker.md` com o tamanho da imagem e os três tempos de reconstrução (nada mudou / código / dependência), **medidos por você**
- [ ] Prova de que o processo roda como `app` e não escreve em `/app` nem em `/etc`
- [ ] Prova de que `docker stop` leva menos de 2 s e termina com código 0
- [ ] O Dockerfile ingênuo guardado em `docker-lab/` como contra-exemplo, com a diferença de tamanho anotada
- [ ] Commit `build: add multi-stage Dockerfile for the Django app`

**3. Desafio (opcional).** Reduza a imagem: mova `grpcio`, `pillow`, `pytest` e outras dependências que **não** são usadas em produção para um grupo (`[dependency-groups]`) e meça o novo tamanho. Depois, escolha o `python:3.13-slim` por *digest* e escreva em `docs/docker.md` como você atualizaria esse *digest* com segurança.

## 🎤 Na entrevista
**1. Como você deixa um build Docker rápido?** Ordenando as instruções do que muda menos para o que muda mais, copiando primeiro os arquivos de dependências e instalando antes de copiar o código, usando cache de camadas e de pacotes, e mantendo o contexto pequeno com `.dockerignore`.

**2. Por que não rodar o container como root?** Porque uma falha na aplicação daria ao invasor privilégios de root dentro do container, que compartilha o kernel com o host. Um usuário sem privilégios reduz o estrago; é uma defesa em camadas.

**3. O que é multi-stage build?** Um Dockerfile com várias etapas (`FROM`), em que a imagem final copia só o necessário das anteriores. Deixa de fora compiladores, caches e arquivos temporários, e a imagem sai menor e com menos superfície de ataque.

## 📚 Para ir além
- 📄 Documentação oficial: [Dockerfile reference](https://docs.docker.com/reference/dockerfile/). Cada instrução, `HEALTHCHECK` e a diferença entre exec e shell form.
- 📄 Documentação oficial: [Best practices for writing Dockerfiles](https://docs.docker.com/build/building/best-practices/). Imagens-base, multi-stage, ordem das camadas, `CMD`/`ENTRYPOINT`.
- 📄 Documentação oficial: [Multi-stage builds](https://docs.docker.com/build/building/multi-stage/) e [Build cache](https://docs.docker.com/build/cache/). Como o cache é invalidado.
- 📄 Documentação oficial: [Build checks](https://docs.docker.com/reference/build-checks/). As regras do `docker build --check` (inclui `JSONArgsRecommended`).
- 📄 Documentação: [uv — Using uv in Docker](https://docs.astral.sh/uv/guides/integration/docker/). Os padrões usados aqui (`--frozen`, cache mount, bytecode).
- 📄 Documentação oficial: [Django — Static files in production](https://docs.djangoproject.com/en/5.2/howto/static-files/deployment/) e [Deployment checklist](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/).
- 🧰 Ferramenta: [hadolint](https://github.com/hadolint/hadolint). Linter de Dockerfile (não executado nesta aula).
- 🏋️ Prática extra: construa a imagem com `python:3.13` (não slim) e com `python:3.13-alpine` e compare tamanho e tempo; anote o que falha no Alpine.

## ✅ Checklist da aula
- [ ] Medi o Dockerfile ingênuo (tamanho, tempo, usuário)
- [ ] Escrevi o Dockerfile multi-stage e entendo cada instrução
- [ ] Sei dizer por que a ordem das camadas importa e medi o ganho
- [ ] A aplicação roda como usuário não root (e não consegue escrever em `/app`)
- [ ] `docker stop` termina em menos de 2 s com código 0
- [ ] `docker build --check` sem avisos
