#!/usr/bin/env bash
# Porta de qualidade: cobertura (linhas + ramos) das CAMADAS DE NEGÓCIO >= 80%. O total do projeto é só informativo.
set -euo pipefail
NEGOCIO="apps/*/services.py,apps/*/domain.py,apps/*/selectors.py,apps/*/repositories.py,apps/*/tasks.py,apps/payments/outbox.py,apps/payments/gateway.py,apps/accounts/lgpd.py,legado/precificacao.py"
uv run pytest -q --cov --cov-branch -p no:randomly > /dev/null
echo "== camadas de negócio (limite 80%)"
uv run coverage report --include="$NEGOCIO" --fail-under=80 --no-skip-covered
echo "== projeto inteiro (informativo)"
uv run coverage report | tail -1
