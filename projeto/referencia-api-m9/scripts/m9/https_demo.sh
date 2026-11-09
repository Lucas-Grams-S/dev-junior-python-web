# HTTPS no laboratório: CA local (openssl), Gunicorn com TLS, e o que o cliente enxerga. Tudo em 127.0.0.1.
set -u
T=scripts/m9/tls
export DEBUG=0 SECRET_KEY=$(python3 -c "import secrets;print(secrets.token_urlsafe(60))") ALLOWED_HOSTS=localhost,127.0.0.1 LOG_LEVEL=ERROR
export SECURE_SSL_REDIRECT=0
uv run gunicorn config.wsgi -b 127.0.0.1:8164 --workers 1 --certfile $T/srv.pem --keyfile $T/srv.key --log-level error > /tmp/gu9_tls.txt 2>&1 &
echo $! > /tmp/gu9_tls.pid
export SECURE_SSL_REDIRECT=1
uv run gunicorn config.wsgi -b 127.0.0.1:8165 --workers 1 --log-level error > /tmp/gu9_plain.txt 2>&1 &
echo $! > /tmp/gu9_plain.pid
sleep 5
echo "== 1) Cliente SEM confiar na CA do laboratório (verificação normal do certificado):"
curl -sS -o /dev/null https://localhost:8164/api/v1/categories/ 2>/tmp/curl9.txt; echo "   código de saída do curl: $? (60 = certificado não verificável)"; head -1 /tmp/curl9.txt | sed 's/^/   /'
echo "== 2) Cliente que confia na CA (--cacert), com o nome certo (localhost):"
curl -sS --cacert $T/ca.pem -o /dev/null -D - https://localhost:8164/api/v1/categories/ 2>&1 | grep -i -E "^HTTP|strict-transport|content-security" | tr -d '\r'
echo "== 3) Nome errado: o certificado só vale para localhost/127.0.0.1 (conecto por 127.0.0.2? -> uso --resolve para forçar outro nome):"
curl -sS --cacert $T/ca.pem --resolve outro.exemplo:8164:127.0.0.1 -o /dev/null https://outro.exemplo:8164/ 2>&1 | head -1
echo "== 4) Versões do TLS (cliente com nível de segurança rebaixado SÓ para este teste):"
python3 scripts/m9/tls_versoes.py 8164 $T/ca.pem
echo "== 5) HTTP puro com SECURE_SSL_REDIRECT=1 (porta 8165):"
curl -s -o /dev/null -D - http://127.0.0.1:8165/api/v1/categories/ | grep -i -E "^HTTP|^location" | tr -d '\r'
echo "== 6) O mesmo servidor exposto DIRETO, com um cabeçalho X-Forwarded-Proto forjado pelo cliente:"
curl -s -o /dev/null -D - -H 'X-Forwarded-Proto: https' http://127.0.0.1:8165/api/v1/categories/ | grep -i -E "^HTTP" | tr -d '\r'
kill -TERM $(cat /tmp/gu9_tls.pid) $(cat /tmp/gu9_plain.pid); wait 2>/dev/null
