# Checkpoint — Módulo 12: CI/CD

> ⏱️ ~1h30 · Faça **sem consultar** as aulas na primeira tentativa. 30 min para o quiz, 60 min para a entrega.

## 📝 Quiz (10 questões)
1. Diferencie **integração contínua**, **entrega contínua** e **implantação contínua**. Qual prática central a CI exige de quem programa?
2. Nomeie e explique **workflow, evento, job, step, runner e action**. Por que cada job começa com `checkout` e como um job entrega algo a outro?
3. Por que o `ci.yml` usa `permissions: contents: read`, `concurrency` com `cancel-in-progress` e `timeout-minutes`? E `UV_FROZEN=1`?
4. Por que **fixar actions por SHA** e como você obteve os SHAs? Cite duas outras defesas de segurança de pipeline (fork, injeção de script).
5. Como validar um workflow **antes** de enviar? O que o actionlint achou de errado no `cd.yml` e por que só apareceria na hora de publicar?
6. Como o job `test` roda contra **PostgreSQL** (service container, `health-cmd`, matriz, expressão `&&/||`)? O que significaram os **4 pulados** e o **aviso** do teardown no PostgreSQL?
7. Por que `docker` tem `needs: [lint, test]`? O que o `smoke_docker.sh` provou num **clone limpo** que não aparecia na sua máquina?
8. Por que separar `ci.yml` de `cd.yml` e dar `packages: write` só ao job `publish`? Como as tags da imagem são calculadas e por que não usar só `latest`?
9. O que são **environments** e o que **não está no YAML**? Descreva dev, staging e produção neste projeto e como a produção é protegida.
10. Compare **recreate, rolling, blue/green, canary** e **feature flag**; explique **como se faz rollback** e por que as migrações precisam ser *expandir e contrair*.

<details><summary>Gabarito</summary>

1. **CI:** integrar com frequência na linha principal e validar cada integração com build automatizado (não publica). **Entrega contínua:** o software está sempre pronto para publicar; uma pessoa aprova/aperta o botão. **Implantação contínua:** publica sozinho tudo o que passa. Quem programa deve integrar pequeno e frequente e tratar a `main` vermelha como prioridade zero.
2. **Workflow:** YAML em `.github/workflows/`. **Evento:** gatilho (`pull_request`, `push`, tag). **Job:** conjunto de steps num runner limpo, em paralelo por padrão. **Step:** `run:` ou `uses:`. **Runner:** a VM (`ubuntu-24.04`). **Action:** passo reutilizável versionado. Cada job é uma máquina nova, sem o código, daí o `checkout`; saídas vão por `outputs`/`needs` e arquivos por artefatos.
3. Menor privilégio no `GITHUB_TOKEN`; um push novo cancela a execução anterior do mesmo PR (economia e fila); um job travado não gasta minutos para sempre; `UV_FROZEN=1` faz o `uv` falhar se o lock estiver desatualizado, em vez de resolver em silêncio (reprodutibilidade).
4. A tag (`@v7`) pode ser movida por quem controla a action; o SHA do commit não (cadeia de suprimentos). Os SHAs vieram de `gh api repos/<action>/releases/latest` e `…/commits/<tag>`, com a versão em comentário e o Dependabot para atualizar. Outras defesas: PR de fork não recebe segredos (evitar `pull_request_target`); dados externos (`github.event.pull_request.title`) passam por `env:`, nunca direto num `run:`.
5. Com o **actionlint** (num repositório Git), mais `shellcheck` nos `run:`. No `cd.yml`, `deploy-production` tinha `needs: deploy-staging` mas lia `needs.publish.outputs.tags`: `property "publish" is not defined…`; um job só lê saídas dos jobs listados em seu próprio `needs`. Correção: `needs: [publish, deploy-staging]`. Só falharia ao publicar.
6. `services: postgres:18` com `--health-cmd pg_isready`, porta mapeada para o runner; matriz `db: [sqlite, postgres]` com `fail-fast: false`; `matrix.include` com uma `database_url` por banco (a versão com `DATABASE_URL` vazia quebrou no GitHub). Resultados: SQLite 302 passed/1 skipped; PostgreSQL 299 passed/4 skipped. Os pulos extras são do código legado com SQL específico do SQLite (legítimos); o aviso (`database "test_minishop" is being accessed by other users`) é uma conexão deixada aberta por algum teste, dívida técnica que só a matriz revelou.
7. Para não gastar tempo construindo a imagem de código reprovado. No clone limpo, o smoke parou no `openssl` porque `nginx/certs/` está no `.gitignore` e não existe num clone; a correção foi `mkdir -p nginx/certs`. Lição: o ambiente limpo testa a sua documentação, e `bash -x` ajuda quando o script morre sem mensagem.
8. O `ci.yml` roda código de qualquer PR e não pode publicar; o `cd.yml` só roda na `main`/tags e só o `publish` tem `packages: write`, com o `GITHUB_TOKEN` temporário. O `metadata-action` gera `sha-abc1234`, nome do branch e semver; `latest` não diz o que está no ar nem permite voltar.
9. Um nome (`staging`, `production`) com segredos, variáveis e regras de proteção (revisores, espera, branches). **Fora do YAML:** os *Required reviewers*, a proteção da branch `main` e os segredos de cada ambiente. Dev = Compose na máquina; staging = automático a cada merge; produção = tag `v*` + aprovação manual.
10. **Recreate:** para e sobe (para a aplicação). **Rolling:** troca réplica a réplica (versões convivem). **Blue/green:** ambiente novo ao lado e vira o tráfego (rollback instantâneo, custo dobrado). **Canary:** pequena fração do tráfego para observar. **Feature flag:** código desligado, ligado por configuração. Rollback = reimplantar a imagem anterior identificada por tag/commit; se a migração foi destrutiva, voltar o código não volta os dados, por isso *expandir e contrair* (adicionar, migrar uso, remover depois, em deploys separados) e backup.
</details>

## 🛠️ Entrega prática
Repositório `minishop` na tag `v3.1-ci`:
- [ ] `.github/workflows/ci.yml` com `lint`, `test` (matriz SQLite/PostgreSQL com service container), `docker` (build, `docker build --check` e smoke), `needs`, `permissions` mínimas, `concurrency`, `timeout-minutes`, `UV_FROZEN` e **actions por SHA**
- [ ] `actionlint` limpo e um `ruim.yml` com 3 erros de propósito e as mensagens em `docs/ci.md`
- [ ] Cada job **reproduzido num `git clone` limpo**, com a tabela de resultados e os **achados** (pulos e aviso do PostgreSQL, `nginx/certs`)
- [ ] `.github/workflows/cd.yml` (GHCR, `packages: write` só no `publish`, `staging`, `production`) e `.github/dependabot.yml`
- [ ] `docs/ci.md` com o diagrama, as configurações **fora do YAML** (branch protegida, environments), a estratégia de deploy e o **procedimento de rollback**
- [ ] Selo de CI no `README.md`
- [ ] **No GitHub:** repositório, PR com checks verdes, um PR vermelho de propósito, `environments` criados, e o registro do que o **seu plano** permite (proteção de branch e revisores só em repositório público/plano pago)
- [ ] Suíte e ferramentas verdes localmente (302 testes; `ruff`, `mypy`, `lint-imports`)
- [ ] Tag publicada: `git tag -a v3.1-ci -m "MiniShop: CI com GitHub Actions" && git push --follow-tags`

**Prova de fogo (40 min, sem consultar):** (1) o CI está verde no PR, mas **quebra na `main`** depois do merge: liste três causas possíveis e como o pipeline deveria evitar cada uma; (2) um colega propõe `on: pull_request_target` para que o CI use um segredo no PR de um fork: explique o risco e uma alternativa; (3) a produção deu erro 500 depois de um deploy: escreva em 6 passos o rollback, incluindo o que verificar sobre migrações.

## 🪞 Autoavaliação
Nota de 0 a 3. Se algum item ficar em **0 ou 1**, refaça a aula antes de seguir.

| Habilidade | Aula | Nota |
|---|---|---|
| CI × entrega × implantação; anatomia de um workflow; segurança do YAML; actionlint | 01 | |
| Matriz com PostgreSQL, `needs`, build e smoke, GHCR, environments, estratégias e rollback | 02 | |

## 🧠 Lógica: lista de verificação
Resolveu sem olhar: tempo de relógio × minutos de runner de um pipeline com matriz e `needs` (12.01), a taxa de erro global em *rolling* e *canary* (12.02)? Marque o que faltou e refaça.

## 🧪 Estado de verificação deste módulo
Validado com o **actionlint**, reproduzido num `git clone` limpo (containers Debian) **e executado no GitHub de verdade** (repositório privado, runners `ubuntu-24.04`, 2026-11-09). Resultados: o **primeiro push reprovou em dois jobs** (formatação dos scripts adicionados depois do laboratório; `DATABASE_URL` definida como string vazia), corrigidos; depois CI **verde** (lint ≈ 28 s, testes em PostgreSQL ≈ 63 s e SQLite ≈ 67 s, imagem e smoke ≈ 84 s); CD publicou a imagem, foi a staging, e **a produção rodou sem aprovação** porque revisores de `environment` e proteção de branch **não estão disponíveis em repositório privado do plano gratuito**; um PR vermelho de propósito ficou `MERGEABLE`; e o Dependabot abriu sozinho um PR de Django 6.1 que o CI reprovou (e a série passou a ser ignorada). No laboratório local: 302 testes em SQLite, 299 + 4 pulados em PostgreSQL 18 (com um aviso de teardown, pendência registrada) e o smoke `SMOKE OK`.

**Não foi executado/verificado:** a imagem no GHCR (o token local não tem `read:packages`), as regras de proteção (indisponíveis no plano), o cache `type=gha` (não conferi acerto de cache) e os **desafios opcionais**. Código em [`projeto/referencia-api-m12/`](../projeto/referencia-api-m12/README.md).

➡️ Próximo: [Módulo 13 — Introdução à nuvem com AWS](../13-aws/README.md).
