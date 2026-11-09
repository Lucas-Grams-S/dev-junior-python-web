# Quantas tentativas de login passam em 1 minuto com 2 workers do Gunicorn? (limite configurado: 5/min)
set -u
export DEBUG=0 SECRET_KEY=$(python3 -c "import secrets;print(secrets.token_urlsafe(60))") ALLOWED_HOSTS=127.0.0.1 SECURE_SSL_REDIRECT=0 LOG_LEVEL=ERROR
rodar() {
  nome=$1
  uv run gunicorn config.wsgi -b 127.0.0.1:8162 --workers 2 --log-level error > /tmp/gu9_$nome.txt 2>&1 &
  echo $! > /tmp/gu9.pid; sleep 4
  codigos=""
  for i in $(seq 1 14); do
    c=$(curl -s -o /dev/null -w "%{http_code}" -X POST -H 'Content-Type: application/json' -H 'X-Forwarded-Proto: https' -d '{"username":"cliente","password":"errada-errada-123"}' http://127.0.0.1:8162/api/v1/auth/token/)
    codigos="$codigos $c"
  done
  kill -TERM $(cat /tmp/gu9.pid); wait 2>/dev/null
  echo "$nome:$codigos"
  echo "   passaram (401): $(echo $codigos | tr ' ' '\n' | grep -c 401) · bloqueadas (429): $(echo $codigos | tr ' ' '\n' | grep -c 429)"
}
echo "limite configurado: login = 5/min; 14 tentativas seguidas contra 2 workers"
rodar "cache_local_por_processo"
export REDIS_CACHE_URL=redis://127.0.0.1:6391/1
docker exec m9-redis redis-cli -n 1 flushdb >/dev/null
rodar "cache_compartilhado_redis"
