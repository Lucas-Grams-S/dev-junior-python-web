#!/usr/bin/env bash
# Definição de pronto (DoD) AUTOMATIZADA: o que a máquina consegue afirmar sobre uma mudança. O resto é revisão humana.
cd "$(dirname "$0")/.."
export DEBUG=${DEBUG:-1}
falhas=0
passo() {  # passo "descrição" comando...
  local descricao=$1; shift
  if "$@" >/tmp/dod_saida.txt 2>&1; then printf "  [x] %s\n" "$descricao"; else printf "  [ ] %s   <-- FALHOU\n" "$descricao"; sed 's/^/        /' /tmp/dod_saida.txt | tail -5; falhas=$((falhas+1)); fi
}
echo "Definição de pronto (parte automática)"
passo "testes passam (todos os níveis, ordem aleatória)"               uv run pytest -q
passo "cobertura das camadas de negócio >= 80%"                         bash scripts/cobertura_negocio.sh
passo "formatação (ruff format)"                                        uv run ruff format --check
passo "lint (ruff check)"                                               uv run ruff check
passo "tipos (mypy)"                                                    uv run mypy
passo "arquitetura (import-linter)"                                     uv run lint-imports
passo "sem migração pendente"                                           uv run python manage.py makemigrations --check --dry-run
passo "contrato OpenAPI válido e sem avisos"                            uv run python manage.py spectacular --validate --fail-on-warn --file /tmp/dod_schema.yml
passo "dependências sem vulnerabilidade conhecida (pip-audit)"          bash -c 'uv export --no-hashes --no-emit-project -o /tmp/dod_req.txt >/dev/null && uv run pip-audit -r /tmp/dod_req.txt --no-deps --disable-pip'
echo "Parte humana (marque no PR): revisão aprovada · critérios de aceitação demonstrados · documentação/ADR atualizados · sem dado pessoal em log"
exit $falhas
