# Cheatsheet: testes, qualidade e colaboração (módulo 10)

> Aulas 10.01 a 10.07. Tudo foi executado no laboratório [`projeto/referencia-api-m10`](../../projeto/referencia-api-m10/README.md).

## Pirâmide e comandos
| Nível | Comando | Para quê |
|---|---|---|
| unidade (sem banco/rede) | `pytest -m unidade` | feedback em ~1 s |
| integração (banco) | `pytest -m integracao` | serviços, repositórios, tarefas |
| API (HTTP) | `pytest -m api` | rotas, permissões, formato de erro |
| tudo, em paralelo | `pytest -n 4` | ganho sublinear; exige testes independentes |
| ordem reproduzível | `pytest -p randomly --randomly-seed=N` | achar dependência entre testes |
| tempo | `pytest --durations=10` | separa `setup` de `call` |

## Escolher o dublê
| Preciso de… | Use |
|---|---|
| respostas prontas | **stub** (ou `return_value`) |
| saber que a chamada aconteceu | **mock** (`assert_called_once_with`) |
| ver o que passou pelo real | **spy** |
| um simulador que funciona (repositório em memória) | **fake** (preferido para o que é seu) |
| que o dublê respeite a interface | `create_autospec(Classe, instance=True)` |
| trocar um nome importado | `monkeypatch.setattr(modulo_que_USA, "nome", ...)` |
| controlar a hora | `monkeypatch.setattr(timezone, "now", ...)` ou injetar `hoje` |

## TDD em uma linha
🔴 um teste pequeno que falha pelo motivo certo → 🟢 o mínimo que passa (pode "fingir") → 🔵 refatorar com tudo verde → repetir; **triangule** e teste a **fronteira**.

## Cobertura
`pytest --cov --cov-branch` · meta **por camada** (ex.: `coverage report --include="apps/*/services.py,..." --fail-under=80`) · cobertura **não** é qualidade: valide por **mutação** (estrague o código e veja o teste falhar; use `PYTHONPYCACHEPREFIX` novo por mutante).

## Ferramentas
```bash
uv run ruff check --fix && uv run ruff format      # lint + formatação (line-length e exceções no pyproject)
uv run mypy                                          # tipos (gradual: estrito só nos módulos puros)
uv run pre-commit install --install-hooks && uv run pre-commit install --hook-type commit-msg --hook-type pre-push
uv run cz check --commit-msg-file .git/COMMIT_EDITMSG
uv run cz bump --dry-run && uv run cz changelog --dry-run
git config blame.ignoreRevsFile .git-blame-ignore-revs
```

## Conventional Commits
`feat` (MINOR) · `fix` (PATCH) · `refactor` · `perf` · `test` · `docs` · `style` · `build` · `ci` · `chore` · `!` ou `BREAKING CHANGE:` (MAJOR) · formatação e lógica em **commits separados**.

## Revisão de código
Ordem: descrição → testes → código. Rótulos: `bloqueante` · `sugestão` · `dúvida` · `nit`. Prove com um **teste que falha**. PR pequeno (< 400 linhas), com descrição e portões verdes.

## IA com responsabilidade
Critérios e testes **antes** · ler o diff · rodar os portões · conferir APIs e **pacotes** (existe? histórico?) · nunca colar segredos ou dados pessoais · você responde pelo que commita.

## Armadilhas
`Mock()` sem spec · patch no alvo errado (e dependente de ordem) · cobertura de linhas sem ramos · `strict` do mypy por módulo · `exclude` do ruff no pre-commit (`force-exclude`) · `.pyc` reaproveitado em mutação manual · uma medição de tempo só.


## Produção e observabilidade (módulo 14)
```bash
curl localhost:8000/health/ ; curl localhost:8000/health/ready/        # liveness / readiness (503 = banco ou cache)
docker compose logs --no-log-prefix web | jq -c 'select(.status >= 500) | {ts,path,request_id}'
curl -H "Authorization: Bearer $METRICS_TOKEN" web:8000/metrics/       # só pela rede interna; Nginx devolve 404 por fora
docker exec redis redis-cli -n 1 --scan --pattern 'catalog:*'          # nunca KEYS * em produção
docker exec pg psql -U m -d m -c "select calls,round(total_exec_time) total_ms,round(mean_exec_time::numeric,2) media_ms,left(query,90) from pg_stat_statements order by total_exec_time desc limit 5"
docker exec pg psql -U m -d m -c "EXPLAIN (ANALYZE, BUFFERS) SELECT ..."   # ANALYZE EXECUTA: use BEGIN/ROLLBACK para escritas
bash scripts/prod/backup.sh "$DATABASE_URL" ./backups 7 && bash scripts/prod/restore_test.sh "$DATABASE_URL" ./backups
```
Regras: JSON com `request_id`; segredo nunca no log; liveness sem dependências; rótulos de métrica = padrão da rota; cache com TTL + invalidação no `on_commit`; falha aberta no geral, fechada no login; ordene `pg_stat_statements` por tempo **total**; backup não testado não é backup.
