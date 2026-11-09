echo "== ruff (regras S, as do bandit) no código do MiniShop, sem tests/seclab/migrations/legado:"
uv run ruff check --isolated --select S --ignore S101,S311 --exclude "tests,seclab,migrations,legado" --output-format concise apps config 2>&1 | grep -v "^\[\*\]\|^No fixes"
echo "== bandit (todas as severidades) em apps e config:"
uv run bandit -r apps config -q --exclude "apps/*/migrations" 2>&1 | grep -E "^>> Issue|Severity|Location" 
