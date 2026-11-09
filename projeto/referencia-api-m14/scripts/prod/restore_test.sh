#!/usr/bin/env bash
# TESTE DE RESTAURAÇÃO (aula 14.04): backup que nunca foi restaurado é esperança. Restaura num banco TEMPORÁRIO, compara as contagens
# com o banco de origem, mede o tempo (o seu RTO medido) e apaga o temporário. Sai com 1 se QUALQUER coisa não bater.
# Uso: bash scripts/prod/restore_test.sh "$DATABASE_URL" /pasta/de/backups [arquivo.dump]   (padrão: o mais recente)
set -euo pipefail
URL="${1:?uso: restore_test.sh DATABASE_URL PASTA [arquivo]}"; BACKUP_DIR="$(cd "$2" && pwd)"; export BACKUP_DIR
source "$(dirname "$0")/pgcli.sh"
ARQ="${3:-$(ls -1 "$BACKUP_DIR"/minishop-*.dump | sort | tail -1)}"; ARQ="$(basename "$ARQ")"
SERVIDOR="$(pgurl_servidor "$URL")"; TEMP="restore_test_$(date -u +%H%M%S)"
falha() { echo "FALHOU: $*" >&2; pgcli psql "$SERVIDOR/postgres" -qc "DROP DATABASE IF EXISTS $TEMP" >/dev/null 2>&1 || true; exit 1; }

echo "1/5 integridade do arquivo (SHA-256)"
( cd "$BACKUP_DIR" && sha256sum -c "$ARQ.sha256" ) || falha "checksum não confere: o arquivo foi alterado ou truncado"
echo "2/5 formato legível (pg_restore --list)"
pgcli pg_restore --list "$BACKUP_DIR/$ARQ" >/dev/null || falha "pg_restore não consegue ler o arquivo"
echo "3/5 restaurar em $TEMP"
INI=$(date +%s.%N)
pgcli psql "$SERVIDOR/postgres" -qc "CREATE DATABASE $TEMP"
pgcli pg_restore --no-owner --exit-on-error -d "$SERVIDOR/$TEMP" "$BACKUP_DIR/$ARQ" || falha "pg_restore falhou"
FIM=$(date +%s.%N)
echo "4/5 conferir contagens (restaurado × faixa registrada no backup)"
ok=1
if [ ! -f "$BACKUP_DIR/$ARQ.counts" ]; then falha "sem $ARQ.counts: não há o que comparar"; fi
while read -r t antes depois; do
  r=$(pgcli psql "$SERVIDOR/$TEMP" -tAc "SELECT count(*) FROM $t" </dev/null)  # </dev/null: o `docker run -i` devoraria o resto do arquivo lido pelo while
  menor=$(( antes < depois ? antes : depois )); maior=$(( antes > depois ? antes : depois ))
  if [ "$r" -ge "$menor" ] && [ "$r" -le "$maior" ]; then s="ok"; else s="DIVERGE"; ok=0; fi
  printf '   %-22s backup=[%s..%s] restaurado=%-8s %s\n' "$t" "$menor" "$maior" "$r" "$s"
done < "$BACKUP_DIR/$ARQ.counts"
echo "5/5 limpeza"
pgcli psql "$SERVIDOR/postgres" -qc "DROP DATABASE $TEMP"
printf '{"event":"restore_test","file":"%s","restore_seconds":%.1f,"ok":%s}\n' "$ARQ" "$(awk "BEGIN{print $FIM - $INI}")" "$([ $ok = 1 ] && echo true || echo false)"
[ $ok = 1 ] || exit 1
