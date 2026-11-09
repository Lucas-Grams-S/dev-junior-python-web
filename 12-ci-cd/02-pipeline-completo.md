# 2. Pipeline completo: lint, testes, build e ambientes

> ⏱️ ~1h30 · Módulo 12 · Pré-requisitos: [12.01](01-conceitos-github-actions.md), [11.06 (Nginx e smoke test)](../11-docker/06-gunicorn-nginx.md), [10.03 (cobertura)](../10-qualidade-testes/03-integracao-api-cobertura.md)

> ✅ **Verificação.** Os workflows passaram pelo **actionlint**, cada job foi reproduzido num `git clone` limpo (containers, PostgreSQL 18 de verdade na matriz) **e tudo foi executado no GitHub de verdade** (repositório privado, runners `ubuntu-24.04`, 2026-11-09): CI, CD, PR vermelho, Dependabot e publicação no GHCR. **Não funcionaram no plano gratuito de repositório privado:** proteção de branch e revisores de `environment` (veja "Execução real"). Não verifiquei diretamente a imagem no GHCR (o token local não tem `read:packages`); o passo de `push` terminou com sucesso. Código em [`projeto/referencia-api-m12/`](../projeto/referencia-api-m12/README.md).

## 🎯 Objetivos
- Montar um pipeline com **lint, testes em matriz (SQLite e PostgreSQL), build da imagem e smoke test**, com dependências entre jobs
- Usar **service containers** para testar contra um PostgreSQL real
- Separar **CI** (valida) de **CD** (publica) e publicar a imagem no **GHCR** com o `GITHUB_TOKEN`
- Descrever **ambientes** (dev, staging, produção), aprovações e **estratégias de deploy** simples, incluindo reversão
- Fechar o marco `v3.1-ci`: pipeline verde em todo PR, com selo no README

## 🤔 Por que isso importa
Lint passando não diz que o código funciona no PostgreSQL de produção, nem que a imagem Docker sobe. O pipeline completo é a **definição de pronto** (aula 10.07) executada por uma máquina: o que cai na `main` já passou por tudo. E é aqui que se decide **como o código chega ao usuário**: quem aprova, em que ordem, e como se volta atrás quando dá errado. Perguntas de entrevista como "como é o fluxo de deploy do seu projeto?" e "como você faz rollback?" se respondem com esta aula.

## 💡 Intuição (explicação simples)
Pense em uma **cozinha de restaurante com várias pessoas**: o ajudante confere os ingredientes (lint), o cozinheiro prova o prato com ingredientes iguais aos do salão (testes com PostgreSQL de verdade), o chefe só autoriza **empratar** (build) se os dois aprovaram, e o prato só **sai para a mesa** (produção) depois do maître (aprovação humana). Se o cliente reclamar, o prato anterior ainda está pronto na bancada para ser servido de novo (rollback).

## 🔬 Como funciona por dentro
```mermaid
flowchart LR
    PR[PR / push] --> L[lint]
    PR --> T1[test: sqlite]
    PR --> T2[test: postgres]
    L & T1 & T2 --> D[docker: build + smoke]
    D -->|merge na main| P[publish: GHCR]
    P --> S[deploy staging<br/>automático]
    S -->|tag v*| PR2[deploy produção<br/>aprovação manual]
```
- **Jobs em paralelo, com `needs`.** `lint` e `test` rodam juntos (feedback rápido); `docker` só começa se os dois passaram (`needs: [lint, test]`), para não gastar 20 minutos construindo uma imagem de código que já reprovou.
- **Matriz.** `strategy.matrix.db: [sqlite, postgres]` cria **duas execuções** do mesmo job. `fail-fast: false` deixa a outra terminar mesmo que uma falhe (você vê as duas respostas).
- **Service containers.** Um bloco `services:` sobe containers (aqui, `postgres:18`) na mesma rede do job, com *health check*; o job só começa quando estão saudáveis. A diferença para o Compose: aqui o job acessa por `localhost:5432` porque as portas são mapeadas para o runner.
- **Por que testar também em PostgreSQL?** O SQLite é o padrão de desenvolvimento, mas **produção usa PostgreSQL**: diferenças em tipos, bloqueios, `ORDER BY` e SQL específico aparecem só lá (o módulo 8 já provou a paridade; agora uma máquina a **vigia**).
- **CI × CD em arquivos separados.** `ci.yml` roda em todo PR e **não tem permissão de publicar**. `cd.yml` roda só na `main` e em tags, e **só** o job `publish` recebe `packages: write`. Quem abre um PR malicioso nunca alcança a publicação.
- **Imagem no GHCR.** O *GitHub Container Registry* guarda imagens junto ao repositório; o login usa o `GITHUB_TOKEN` do próprio workflow (nada de senha cadastrada). O `docker/metadata-action` calcula as *tags* (`sha-abc1234`, `main`, `1.2.3`). **Identifique a imagem pelo commit** (`sha-…`), nunca só por `latest`: é o que permite saber o que está no ar e voltar.
- **Ambientes (*environments*).** Um nome (`staging`, `production`) ao qual se atribuem **segredos, variáveis e regras de proteção** (revisores obrigatórios, espera, restrição de branches). Um job com `environment: production` **pausa** até alguém aprovar. Isso é a "entrega contínua com botão": o código chega pronto, uma pessoa decide.
  | Ambiente | Para quê | Quando recebe |
  |---|---|---|
  | **dev** (local/Compose) | desenvolver | sempre; é a sua máquina |
  | **staging** | cópia da produção para validar de ponta a ponta, sem usuários reais | automático a cada merge na `main` |
  | **produção** | usuários reais | tag de versão + aprovação |
- **Estratégias de deploy** (visão geral):
  | Estratégia | Como é | Prós | Contras |
  |---|---|---|---|
  | **Recreate** | para a versão antiga, sobe a nova | simples | **indisponibilidade** durante a troca |
  | **Rolling** | troca réplica por réplica | sem parada, sem infra dupla | duas versões convivem por um tempo |
  | **Blue/green** | sobe o ambiente novo inteiro ao lado e vira o tráfego de uma vez | **rollback instantâneo** (volta o tráfego) | infraestrutura dobrada |
  | **Canary** | manda 1-5% do tráfego à versão nova e observa | risco pequeno, detecção cedo | exige métricas e roteamento |
  | **Feature flag** | o código novo vai desligado e liga-se por configuração | separa *deploy* de *release* | mais ramificações de código |
  Para o MiniShop de um servidor (módulo 13) o realista é **recreate** ou **rolling** com Compose; o importante é a **reversão**: reimplantar a imagem anterior (`sha-…`). Para isso funcionar, **migrações de banco precisam ser compatíveis com a versão anterior** durante a troca (padrão *expandir e contrair*: primeiro adiciona a coluna, depois o código passa a usá-la, depois se remove a antiga, em deploys separados).

## 🛠️ Exemplo prático
**1. `ci.yml` completo** (`.github/workflows/ci.yml`; a parte do `lint` é a da aula 01, acrescida de migrações, OpenAPI e `pip-audit`):
```yaml
jobs:
  lint:
    # ... checkout, setup-uv, uv sync, ruff, mypy, lint-imports ...
      - run: uv run python manage.py makemigrations --check --dry-run
      - run: uv run python manage.py spectacular --validate --fail-on-warn --file /tmp/schema.yml
      - name: Dependências sem vulnerabilidade conhecida
        run: |
          uv export --no-hashes --no-emit-project -o /tmp/requirements.txt
          uv run pip-audit -r /tmp/requirements.txt --no-deps --disable-pip

  test:
    name: Testes (${{ matrix.db }})
    runs-on: ubuntu-24.04
    timeout-minutes: 15
    strategy:
      fail-fast: false
      matrix:
        include:
          - db: sqlite
            database_url: sqlite:///ci-test.sqlite3
          - db: postgres
            database_url: postgres://minishop:ci-somente-teste@localhost:5432/minishop
    services:
      postgres:
        image: postgres:18
        env:
          POSTGRES_USER: minishop
          POSTGRES_PASSWORD: ci-somente-teste
          POSTGRES_DB: minishop
        ports: ["5432:5432"]
        options: >-
          --health-cmd "pg_isready -U minishop -d minishop"
          --health-interval 5s --health-timeout 3s --health-retries 10
    env:
      DATABASE_URL: ${{ matrix.database_url }}
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1  # v7.0.1
      - uses: astral-sh/setup-uv@68559e99cc807c1eb7e9238fd43a15bba460eec2  # v10.3.3
        with: { python-version: "3.13", enable-cache: true }
      - run: uv sync
      - name: Suíte completa
        run: uv run pytest -q
      - name: Porta de cobertura (camadas de negócio >= 80%)
        if: matrix.db == 'sqlite'
        run: bash scripts/cobertura_negocio.sh

  docker:
    name: Imagem Docker e smoke test
    runs-on: ubuntu-24.04
    needs: [lint, test]          # só constrói se a qualidade passou
    timeout-minutes: 20
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1  # v7.0.1
      - uses: docker/setup-buildx-action@f87e5991a6d7451dcb8d9637bfbc97413f497069  # v4.4.1
      - name: Dockerfile sem avisos
        run: docker build --check .
      - name: Construir a imagem (sem publicar)
        uses: docker/build-push-action@c3c9e263c25d99ce0380d002d59b67737d91b0dc  # v7.4.0
        with:
          context: .
          push: false
          load: true
          tags: minishop:ci
          cache-from: type=gha
          cache-to: type=gha,mode=max
      - name: Smoke test com Docker Compose
        run: |
          cp .env.docker.example .env
          bash scripts/smoke_docker.sh
```
O `matrix.include` associa a cada banco a sua `DATABASE_URL` (um SQLite descartável ou o service container). **Atenção:** a primeira versão deste arquivo definia `DATABASE_URL` como *vazia* para o SQLite; ela passou no laboratório (lá a variável simplesmente não existia) e **quebrou no GitHub**: ver "Execução real". Os segredos do banco de teste são **valores descartáveis**, sem relação com os de produção; não há segredo real em `ci.yml`.

**2. Executando cada job (no clone limpo).**
```bash
# test / sqlite
DEBUG=1 UV_FROZEN=1 uv sync && uv run pytest -q
# test / postgres: um PostgreSQL 18 numa rede de teste
docker network create ci12-net
docker run -d --name ci12-pg --network ci12-net -e POSTGRES_USER=minishop -e POSTGRES_PASSWORD=ci-somente-teste -e POSTGRES_DB=minishop postgres:18
DATABASE_URL=postgres://minishop:ci-somente-teste@ci12-pg:5432/minishop uv run pytest -q
# cobertura
bash scripts/cobertura_negocio.sh
```
```text
sqlite:    302 passed, 1 skipped, 1 xfailed in 11.64s
postgres:  299 passed, 4 skipped, 1 xfailed, 1 warning in 21.06s
cobertura: camadas de negócio TOTAL 98% (limite 80%) · projeto inteiro 96%
```
**Duas coisas para ler com atenção.** (1) Os **3 testes a mais "pulados"** no PostgreSQL são do código legado que usa SQL específico do SQLite (`SKIPPED … legado usa SQL específico do SQLite`): é um pulo **legítimo e documentado**, mas se aparecer um pulo novo na matriz, é para investigar. (2) O **aviso** `Error when trying to teardown test databases: OperationalError('database "test_minishop" is being accessed by other users')`: no PostgreSQL, alguma conexão ficou aberta ao fim (provável teste de concorrência com *threads*). Não reprova, mas é uma **dívida técnica real** que só a matriz com PostgreSQL revelou; vale registrar numa issue. O PostgreSQL também levou quase o dobro do tempo (21 s × 11,6 s): o SQLite em memória é mais rápido, e por isso é o padrão do desenvolvimento, e o PostgreSQL o árbitro final.

**3. O job `docker`, num clone limpo.**
```bash
docker build --check .
cp .env.docker.example .env && bash scripts/smoke_docker.sh
```
```text
Check complete, no warnings found.
== 2/6 dados de exemplo (seed) — só em desenvolvimento
Seed ok: 64 produtos
carrinho -> 201
pedido -> 201
ok: web roda como 'app'; estático servido pelo Nginx
SMOKE OK                                          (32 s)
```
Mas a **primeira** tentativa nesse clone limpo **falhou sem nenhuma mensagem**: o script parou no `openssl` porque a pasta `nginx/certs/` não existe num clone (ela está no `.gitignore`, junto com o `.gitkeep`). No meu computador sempre existiu. É exatamente o tipo de erro que só a CI (ou um clone limpo) revela; a correção foi uma linha no script (`mkdir -p nginx/certs`). Dois aprendizados: **o ambiente do CI é o teste da sua documentação**; e `set -e` sem mensagem torna a falha difícil de achar (por isso o `bash -x`: `+ openssl req …` foi a última linha impressa).

**4. `cd.yml`: publicar e passar pelos ambientes.**
```yaml
name: CD
on:
  push:
    branches: [main]
    tags: ["v*"]
permissions:
  contents: read
concurrency:
  group: cd-${{ github.ref }}
  cancel-in-progress: false      # um deploy em andamento não deve ser cancelado no meio

jobs:
  publish:
    name: Publicar a imagem no GHCR
    runs-on: ubuntu-24.04
    permissions:
      contents: read
      packages: write            # só ESTE job pode publicar pacotes
    outputs:
      tags: ${{ steps.meta.outputs.tags }}
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1  # v7.0.1
      - uses: docker/setup-buildx-action@f87e5991a6d7451dcb8d9637bfbc97413f497069  # v4.4.1
      - uses: docker/login-action@8aa5831fb8d48d8f76594c7ddde61ae58019f550  # v4.8.0
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}     # token temporário do próprio workflow
      - id: meta
        uses: docker/metadata-action@dc802804100637a589fabce1cb79ff13a1411302  # v6.2.0
        with:
          images: ghcr.io/${{ github.repository }}
          tags: |
            type=sha,format=short
            type=ref,event=branch
            type=semver,pattern={{version}}
      - uses: docker/build-push-action@c3c9e263c25d99ce0380d002d59b67737d91b0dc  # v7.4.0
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  deploy-staging:
    needs: publish
    runs-on: ubuntu-24.04
    environment: staging          # variáveis e segredos DESTE ambiente
    steps:
      - name: Deploy (o passo real chega no módulo 13)
        run: echo "Subiria ${{ needs.publish.outputs.tags }} em staging"

  deploy-production:
    needs: [publish, deploy-staging]
    if: startsWith(github.ref, 'refs/tags/v')      # só tags de versão chegam à produção
    runs-on: ubuntu-24.04
    environment: production       # com "Required reviewers": o job PAUSA até alguém aprovar
    steps:
      - name: Deploy (o passo real chega no módulo 13)
        run: echo "Subiria ${{ needs.publish.outputs.tags }} em produção"
```
**O actionlint achou um erro meu aqui.** Na primeira versão eu escrevi `needs: deploy-staging` no `deploy-production` e usei `needs.publish.outputs.tags`:
```text
cd.yml:68:32: property "publish" is not defined in object type {deploy-staging: {outputs: {}; result: string}} [expression]
```
Um job só enxerga as saídas dos jobs listados em **seu** `needs` (e não transitivamente). Correção: `needs: [publish, deploy-staging]`. Teria falhado só na hora de publicar. Os passos de deploy são `echo` **de propósito**: o deploy real (SSH/EC2, ECS) é do módulo 13, e nenhum segredo de nuvem existe ainda. O que o módulo 12 entrega é o **caminho**: publicar → staging → (tag) → produção com aprovação.

**5. Dependabot** (`.github/dependabot.yml`; a versão final tem um `ignore`, veja "Execução real"): abre PRs semanais para atualizar dependências do `uv`, as *actions* (os SHAs fixados!) e a imagem do Docker. Cada PR passa pelo mesmo CI: se quebrar, você vê **antes** de aceitar.
```yaml
version: 2
updates:
  - package-ecosystem: "uv"
    directory: "/"
    schedule: { interval: "weekly" }
    open-pull-requests-limit: 5
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule: { interval: "weekly" }
  - package-ecosystem: "docker"
    directory: "/"
    schedule: { interval: "weekly" }
```
(Executado de verdade: ver "Execução real".)

**6. O que transforma o CI em *porta*: proteção de branch (indisponível no plano gratuito privado, veja "Execução real").** Sem ela, o vermelho é só um aviso. Em *Settings → Branches* (ou *Rulesets*): exigir PR, exigir os *checks* `Lint, tipos e arquitetura`, `Testes (sqlite)`, `Testes (postgres)` e `Imagem Docker e smoke test`, exigir branch atualizada e (em time) uma aprovação. Também há API (`gh api repos/OWNER/REPO/branches/main/protection -X PUT …`); confira a doc antes de usar. E em *Settings → Environments*: criar `staging` e `production`, e em `production` marcar *Required reviewers*.

**7. O selo (*badge*) no README.**
```markdown
[![CI](https://github.com/SEU-USUARIO/minishop/actions/workflows/ci.yml/badge.svg)](https://github.com/SEU-USUARIO/minishop/actions/workflows/ci.yml)
```
Troque `SEU-USUARIO` pelo seu usuário; o selo fica verde/vermelho conforme a última execução na `main`. Para o portfólio (módulo 16) ele vale mais que a frase "tem testes".

**8. Reversão.** Com imagens identificadas pelo commit, o rollback é um deploy da tag anterior:
```bash
git tag -a v3.1.1 -m "fix: ..." && git push origin v3.1.1     # dispara o cd.yml: publica ghcr.io/…:3.1.1 e :sha-abc1234
# deu errado em produção? reimplante a versão anterior (no módulo 13: docker compose pull/up com a tag antiga)
```
Banco: se a versão nova rodou uma migração **destrutiva**, voltar o código não volta os dados. Por isso: migrações compatíveis (expandir e contrair) e backup antes de mudanças arriscadas (módulo 14).

## 🚀 Execução real no GitHub (2026-11-09)
Criei um repositório **privado** (`gh repo create minishop --private --source=. --push`) e fiz o primeiro push na `main`. O que aconteceu, em ordem:

**1. O CI reprovou, e os dois defeitos eram de verdade.**
```text
Lint, tipos e arquitetura   failure   ← uv run ruff format --check
Testes (postgres)           success
Testes (sqlite)             failure   ← ImportError: DATABASE_URL com esquema não suportado: ''
Imagem Docker e smoke test  skipped   (needs: lint, test)
```
- **`ruff format --check` reprovou 6 arquivos**: os scripts auxiliares do módulo 11 que eu **adicionei à pasta depois** de rodar o laboratório. Não os submeti à mesma verificação. Lição: *toda* mudança passa pelo pipeline, inclusive "só uns scripts"; e é por isso que o CI existe. (Corrigi com `ruff format`, e o `S310` de `urlopen` nos scripts de laboratório ganhou uma exceção **justificada** em `per-file-ignores`.)
- **`DATABASE_URL` definida como string vazia.** No laboratório a variável não existia (o `settings.py` usa o padrão SQLite); no GitHub, `DATABASE_URL: ''` **existe e é vazia**, e `os.environ.get("DATABASE_URL", padrao)` devolve `''` e não o padrão. Duas correções: o workflow passou a usar `matrix.include` com uma URL por banco; e o `settings.py` passou a tratar variável vazia como não definida (`os.environ.get("DATABASE_URL") or padrao`), porque variáveis vazias são comuns em CI e Compose (`${VAR:-}`).
O job de PostgreSQL passou na primeira tentativa, e o `docker` ficou `skipped` por causa do `needs`: o pipeline fez o que foi desenhado.

**2. Verde, com tempos reais** (runners hospedados, segunda execução):
| Job | Tempo |
|---|---|
| Lint, tipos e arquitetura | ≈ 28 s |
| Testes (postgres) | ≈ 63 s |
| Testes (sqlite) | ≈ 67 s |
| Imagem Docker e smoke test | ≈ 84 s (depois dos dois anteriores) |
Total de relógio ≈ 2 min 30 s. Compare com o laboratório (testes em 11 s e 21 s): o runner é bem mais lento, porque inclui preparar a máquina, `uv sync` e o PostgreSQL em container.

**3. CD.** Na `main`: `Publicar a imagem no GHCR` → `Deploy em staging` com sucesso, e `Deploy em produção` **pulado** (não é tag). Criei a tag `v3.1-ci` (`git tag -a … && git push origin v3.1-ci`): publicar → staging → **produção rodou em 5 s, sem pedir aprovação**. Porque...

**4. ...proteção de branch e revisores de `environment` não existem em repositório privado do plano gratuito.** As chamadas de API retornaram:
```text
Upgrade to GitHub Pro or make this repository public to enable this feature.      (proteção de branch, 403)
Failed to create the environment protection rule. Please ensure the billing plan supports the required reviewers protection rule.   (422)
```
Na prática, **o `environment: production` sem revisores não protege nada**: o job roda direto. Repare que o YAML estava "certo" e a produção ainda assim foi implantada sem ninguém aprovar. Para ter as proteções: repositório público, plano pago ou uma organização. Eu **não** tornei o repositório público (decisão sua). Enquanto isso, a defesa possível é o *fluxo*: só tags `v*` chegam a produção e só você cria tags.

**5. PR vermelho de propósito (`import os` sem uso).**
```text
Lint, tipos e arquitetura   fail
Testes (postgres)           pass
Testes (sqlite)             pass
Imagem Docker e smoke test  skipping
mergeable=MERGEABLE state=UNSTABLE
```
O PR **ficou vermelho e ainda assim "mesclável"**: sem proteção de branch, o vermelho é só um aviso. É exatamente o que a seção 6 descreve, agora comprovado. Fechei o PR sem mesclar.

**6. O Dependabot, sem eu pedir.** Poucos minutos depois do primeiro push, ele abriu o PR **"bump django from 5.2.19 to 6.1.3"**, que **alargava a restrição** (`django>=5.2,<5.3` → `<6.2`). O CI o reprovou (lint e testes em SQLite; os de PostgreSQL passaram): o CI funcionou como juiz. Como o curso está na série LTS 5.2, adicionei ao `dependabot.yml`:
```yaml
    ignore:
      - dependency-name: "django"
        versions: [">=5.3"]        # trocar de série é uma decisão, não um PR automático
```
e fechei o PR com um comentário explicando. Lição: dependências de *série* precisam de regra explícita; PRs automáticos não decidem por você.

**7. Detalhes que valem anotar.** (a) A tag `v3.1-ci` não é *semver*, então o `metadata-action` só gerou a tag `sha-…` (o padrão `type=semver` só age com `v1.2.3`); para versões de verdade use `v3.1.0`. (b) O nome da imagem no GHCR precisa ser minúsculo (`ghcr.io/lucas-grams-s/minishop`); o `metadata-action` normaliza, mas um `docker pull` à mão não. (c) O GitHub abriu os fluxos do Dependabot como *runs* na lista: não é erro.

## 🧠 Pausa para lógica
**Problema.** Um deploy *rolling* troca 4 réplicas, uma por vez. A versão nova tem um bug que causa erro 500 em 10% das requisições que ela atende. (a) Se o balanceador distribui igualmente, qual a taxa de erro global quando 1, 2, 3 e 4 réplicas já estão na versão nova? (b) Com *canary* de 5% do tráfego, qual a taxa global de erro? (c) Em qual das duas estratégias você detecta o problema com menos usuários afetados, e o que precisa existir para detectar?

<details><summary>Dica</summary>Taxa global = fração do tráfego na versão nova × 10%.</details>

<details><summary>Solução comentada</summary>

(a) 25% × 10% = **2,5%**, depois **5%**, **7,5%** e **10%**: o erro cresce a cada etapa, a menos que alguém interrompa o rollout. (b) 5% × 10% = **0,5%** de erro global. (c) O *canary*: expõe poucos usuários **e** para ali. Mas em ambos é preciso **observar**: métricas de erro por versão e um critério de parada (módulo 14); sem observabilidade, o canary é só um rolling mais lento. Um bom rolling também pára sozinho se o *health check* das réplicas novas falhar.
</details>

## ⚠️ Erros comuns e boas práticas
| Sintoma / mensagem | Causa | Solução |
|---|---|---|
| `property "x" is not defined in object type {…}` (actionlint) | Usou `needs.x` sem listar `x` em `needs:` | Listar todos os jobs de que lê saídas |
| Testes passam em SQLite e falham em PostgreSQL | Diferença de SQL/tipos/bloqueios | A matriz existe para isso; corrigir o código, não pular o teste |
| `connection refused` ao PostgreSQL do job | Service container ainda subindo | `--health-cmd` nas `options` (o job espera ficar saudável) |
| `denied: permission_denied: write_package` | Job sem `packages: write` | Permissão **no job** `publish` |
| Imagem enviada com a tag `latest` e ninguém sabe qual é | Tag mutável | `type=sha` + semver; `latest` só como atalho |
| Smoke test falha só no CI | Dependência do seu ambiente (pasta ignorada, variável) | Clone limpo; `bash -x` |
| Deploy de produção sem aprovação | `environment` sem *Required reviewers* | Configurar no repositório (não está no YAML!) |
| PR aprovado com CI vermelho | Sem proteção de branch | Exigir os *checks* nomeados |
| Dependência atualizada quebra o build | Atualização manual e esquecida | Dependabot + CI como juiz |
| Segredo de produção usado em PR | Segredo no nível do repositório | Segredos **por ambiente** (`environments`) |
| Pipeline lento | Tudo em série, sem cache | `needs` só onde necessário, cache, matriz enxuta |
| Rollback impossível | Migração destrutiva ou imagem sem identificação | Expandir/contrair; tag por commit |

- **A `main` deve estar sempre verde.** Se quebrar, desfaça (`git revert`) primeiro, investigue depois.
- **O pipeline é código:** versionado, revisado em PR, validado (actionlint) e com dono.
- **Ordem do barato para o caro:** lint (segundos) → testes (minutos) → imagem/smoke (mais minutos) → deploy.
- **Staging parecido com produção**: mesma imagem, mesma configuração (por variáveis), banco do mesmo tipo.
- **Segredos por ambiente e nunca em log**; a produção só com aprovação humana.
- **Documente o que não está no YAML** (proteção de branch, revisores do ambiente) em `docs/ci.md`.

## 🧩 Exercícios
**1. Fixação.** (a) Por que `docker` tem `needs: [lint, test]`? (b) O que o `fail-fast: false` muda? (c) Por que separar `ci.yml` de `cd.yml` e dar `packages: write` só ao job `publish`? (d) Rolling × blue/green. (e) O que garante que o rollback seja possível?

<details><summary>Solução</summary>

(a) Para não construir a imagem de um código que já reprovou. (b) As outras combinações da matriz continuam mesmo que uma falhe: você vê todos os resultados. (c) O CI roda código de PRs (inclusive de terceiros); só a esteira que roda na `main` deve poder publicar. (d) Rolling troca réplica a réplica (sem infra dupla, versões convivem); blue/green sobe tudo ao lado e vira o tráfego (rollback instantâneo, infra dobrada). (e) Imagens identificadas por commit/versão, e migrações compatíveis com a versão anterior.
</details>

**2. Aplicação no projeto MiniShop (fecha o marco `v3.1-ci`).**
- [ ] `ci.yml` com `lint`, `test` (matriz SQLite e PostgreSQL 18 com service container), `docker` (`docker build --check`, build, smoke), `needs` correto e `actionlint` limpo
- [ ] Cada job **reproduzido** num `git clone` limpo, com a tabela de resultados (302 / 299 + 4 pulados, cobertura 98%) e **a explicação dos pulos e do aviso** do PostgreSQL
- [ ] O defeito do `nginx/certs` (ou outro que você achar) registrado como **achado do clone limpo**
- [ ] `cd.yml` com `publish` (GHCR, `packages: write` só no job), `deploy-staging` e `deploy-production` (`environment`), sem segredos
- [ ] `dependabot.yml` para `uv`, `github-actions` e `docker`
- [ ] `docs/ci.md`: diagrama do pipeline, as regras de proteção de branch e de ambientes a configurar, a estratégia de deploy escolhida e o **procedimento de rollback**
- [ ] Selo no README (com o seu usuário)
- [ ] No GitHub: repositório (privado), PR com os **checks verdes**, e um PR **vermelho de propósito**; anote se a proteção de branch está disponível no seu plano
- [ ] `git tag -a v3.1-ci -m "MiniShop: CI com GitHub Actions"` (veja o [checkpoint](checkpoint.md))
- [ ] Commit `ci: add full pipeline, delivery workflow and dependabot`

**3. Desafio (opcional).** Adicione um job `migracoes-no-postgres` que sobe o PostgreSQL, aplica `migrate` **a partir do esquema da versão anterior** (uma tag antiga) e depois com a versão nova, para comprovar que a migração é compatível (o padrão expandir/contrair). Descreva o que reprovaria o job.

## 🎤 Na entrevista
**1. Como é o pipeline do seu projeto?** A cada PR roda lint, tipos, checagem de migrações, auditoria de dependências, testes em SQLite e PostgreSQL com cobertura mínima e, se tudo passar, o build da imagem com um smoke test em Compose. Na `main`, a imagem é publicada no registro com tag do commit, vai a staging sozinha, e a produção exige tag de versão e aprovação humana.

**2. Como você faz rollback?** Reimplantando a imagem anterior, identificada por tag de versão/commit. Funciona porque as imagens são imutáveis e as migrações de banco são compatíveis com a versão anterior (expandir e contrair); mudanças destrutivas pedem backup e planejamento próprio.

**3. Qual a diferença entre rolling, blue/green e canary?** Rolling troca as instâncias aos poucos; blue/green mantém dois ambientes completos e vira o tráfego de uma vez (rollback imediato, custo dobrado); canary envia uma pequena fração do tráfego à nova versão para observar antes de ampliar.

## 📚 Para ir além
- 📄 Documentação oficial: [Service containers](https://docs.github.com/en/actions/using-containerized-services/about-service-containers). `services:`, portas e *health checks* (em inglês).
- 📄 Documentação oficial: [Ambientes (*environments*)](https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments) e [Revisão de deployments](https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/review-deployments). Revisores obrigatórios e segredos por ambiente (em inglês).
- 📄 Documentação oficial: [Publicar imagens Docker](https://docs.github.com/en/actions/use-cases-and-examples/publishing-packages/publishing-docker-images) e [Docker — GitHub Actions](https://docs.docker.com/build/ci/github-actions/). GHCR, `metadata-action`, cache `gha`.
- 📄 Documentação oficial: [Branches protegidos](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches). Exigir *checks* e revisões.
- 📄 Documentação oficial: [Dependabot — opções](https://docs.github.com/en/code-security/dependabot/working-with-dependabot/dependabot-options-reference). Ecossistemas e agenda.
- 📄 Artigo: [Martin Fowler — Blue/Green Deployment](https://martinfowler.com/bliki/BlueGreenDeployment.html) e [Canary Release](https://martinfowler.com/bliki/CanaryRelease.html) (em inglês).
- 📄 Referência: [Trunk Based Development](https://trunkbaseddevelopment.com/). O fluxo de branch que combina com CI frequente (em inglês).
- 🧰 Ferramenta: [actionlint](https://github.com/rhysd/actionlint). Rode antes de cada commit em `.github/`.
- 🏋️ Prática extra: simule um deploy ruim: publique uma "versão 2" que falha no `/admin/login/` e use o `healthcheck` (aula 11.05) para barrar a troca; descreva como o *rolling* se comportaria.

## ✅ Checklist da aula
- [ ] Pipeline com lint, testes em matriz, build e smoke, com `needs`
- [ ] Testei contra PostgreSQL de verdade e entendi pulos e avisos
- [ ] CI e CD em arquivos separados, com permissões mínimas por job
- [ ] Sei o que são `environments`, aprovações e as estratégias de deploy
- [ ] Sei fazer e explicar um rollback
- [ ] Selo no README e `docs/ci.md` escritos
