#!/usr/bin/env bash
# Teste de fumaça do MiniShop em containers: sobe tudo, faz um pedido pelo Nginx e confere o e-mail do worker.
# Uso: bash scripts/smoke_docker.sh [--manter]   (por padrão derruba tudo e apaga os volumes DESTE projeto)
set -euo pipefail
cd "$(dirname "$0")/.."

COMPOSE=(docker compose -f compose.yaml -f compose.asgi.yaml)
BASE=https://127.0.0.1:8443/api/v1
export COMPOSE_PROGRESS=quiet
passo() { printf '\n== %s\n' "$*"; }
falhar() { printf 'FALHOU: %s\n' "$*" >&2; "${COMPOSE[@]}" logs --tail 30 >&2; exit 1; }

[ -f .env ] || falhar "crie o .env (copie de .env.docker.example)"
mkdir -p nginx/certs
[ -f nginx/certs/dev.crt ] || openssl req -x509 -newkey rsa:2048 -nodes -days 30 -subj "/CN=localhost" \
    -keyout nginx/certs/dev.key -out nginx/certs/dev.crt 2>/dev/null

passo "1/6 subir tudo (build + espera ficar saudável)"
"${COMPOSE[@]}" up -d --build --wait --quiet-pull

passo "2/6 dados de exemplo (seed) — só em desenvolvimento"
"${COMPOSE[@]}" run --rm -e DEBUG=1 web python manage.py seed

passo "3/6 login"
TOKEN=$(curl -sk -X POST "$BASE/auth/token/" -H 'Content-Type: application/json' \
        -d '{"username":"cliente","password":"dev-somente-local-123"}' | python3 -c 'import sys,json;print(json.load(sys.stdin)["access"])')
[ -n "$TOKEN" ] || falhar "sem token"
H="Authorization: Bearer $TOKEN"

passo "4/6 carrinho e pedido (chave de idempotência nova a cada execução)"
PRODUTO=$(curl -sk -H "$H" "$BASE/products/" | python3 -c 'import sys,json;print(json.load(sys.stdin)["results"][0]["id"])')
curl -sk -o /dev/null -w 'carrinho -> %{http_code}\n' -X POST "$BASE/cart/items/" -H "$H" -H 'Content-Type: application/json' -d "{\"product\":$PRODUTO,\"quantity\":1}"
CODIGO=$(curl -sk -o /tmp/pedido.json -w '%{http_code}' -X POST "$BASE/orders/" -H "$H" -H "Idempotency-Key: smoke-$(date +%s)" -H 'Content-Type: application/json' -d '{}')
echo "pedido -> $CODIGO"; [ "$CODIGO" = 201 ] || falhar "pedido não foi criado"

passo "5/6 e-mail de confirmação enviado pelo worker"
for _ in $(seq 1 15); do
  "${COMPOSE[@]}" exec -T worker sh -c 'test -s /data/outbox.jsonl' 2>/dev/null && break || sleep 1
done
"${COMPOSE[@]}" exec -T worker tail -n 1 /data/outbox.jsonl | cut -c1-120 || falhar "o worker não gravou o e-mail"

passo "6/6 usuário do processo e arquivos estáticos"
"${COMPOSE[@]}" exec -T web id -un | grep -qx app || falhar "o web não roda como usuário 'app'"
[ "$(curl -sk -o /dev/null -w '%{http_code}' https://127.0.0.1:8443/static/admin/css/base.css)" = 200 ] || falhar "estático não serviu"
echo "ok: web roda como 'app'; estático servido pelo Nginx"

if [ "${1:-}" != "--manter" ]; then
  passo "limpeza (somente o projeto minishop-docker)"; "${COMPOSE[@]}" down -v
fi
printf '\nSMOKE OK\n'
