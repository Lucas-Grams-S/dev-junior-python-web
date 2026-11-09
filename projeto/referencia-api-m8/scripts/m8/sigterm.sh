set -u
export DEBUG=0 SECRET_KEY=$(python3 -c "import secrets;print(secrets.token_urlsafe(60))") ALLOWED_HOSTS=127.0.0.1 SECURE_SSL_REDIRECT=0 LOG_LEVEL=INFO
export DATABASE_URL=postgres://postgres:lab@127.0.0.1:5499/minishop_m8 PYTHONPATH=scripts/m8
uv run gunicorn lenta_wsgi:application -b 127.0.0.1:8161 --workers 1 --graceful-timeout 10 --access-logfile - > /tmp/gunicorn_m8.txt 2>&1 &
echo $! > /tmp/gu_m8.pid; sleep 4
echo "== requisição normal (HSTS/HTTPS atrás de proxy):"
curl -s -o /dev/null -w "categories -> %{http_code}\n" -H 'X-Forwarded-Proto: https' http://127.0.0.1:8161/api/v1/categories/
echo "== requisição lenta em andamento + SIGTERM após 1 s:"
( curl -s -w "resposta da lenta: %{http_code} em %{time_total}s\n" http://127.0.0.1:8161/lenta ) &
sleep 1; kill -TERM $(cat /tmp/gu_m8.pid); T=$(date +%s.%N)
wait; echo "processo encerrou depois de $(python3 -c "print(round($(date +%s.%N)-$T,1))")s do SIGTERM"
echo "== curl após encerrar:"; curl -s -o /dev/null -w "%{http_code}\n" -m 2 http://127.0.0.1:8161/lenta || echo "conexão recusada (já saiu)"
echo "== o que o gunicorn escreveu em stdout:"; sed 's/^\[[^]]*\] //' /tmp/gunicorn_m8.txt
