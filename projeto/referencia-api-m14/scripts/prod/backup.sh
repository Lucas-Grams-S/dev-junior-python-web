#!/usr/bin/env bash
# Backup LÓGICO do PostgreSQL (aula 14.04): pg_dump -Fc + checksum + verificação de leitura + retenção. Imprime UMA linha JSON.
# Uso: bash scripts/prod/backup.sh "$DATABASE_URL" /pasta/de/backups [QUANTOS_MANTER=7]
#      BACKUP_S3_URI=s3://meu-bucket-de-backups/minishop  → também envia ao S3 (cifrado no destino)
set -euo pipefail
URL="${1:?uso: backup.sh DATABASE_URL PASTA [manter]}"; BACKUP_DIR="$(mkdir -p "$2" && cd "$2" && pwd)"; MANTER="${3:-7}"
export BACKUP_DIR
source "$(dirname "$0")/pgcli.sh"

TS=$(date -u +%Y%m%dT%H%M%SZ); NOME="minishop-$TS.dump"; INI=$(date +%s)
TABELAS="${TABELAS:-catalog_product catalog_category accounts_user orders_order orders_orderitem}"
# Contagens ANTES e DEPOIS do dump: o instantâneo do pg_dump fica entre as duas, então o teste de restauração usa a faixa [antes, depois]
# (comparar com o banco "ao vivo" na hora do teste daria falso alarme: o banco continua recebendo escritas depois do backup).
contar() { for t in $TABELAS; do echo "$t $(pgcli psql "${URL%%\?*}" -tAc "SELECT count(*) FROM $t")"; done; }
ANTES=$(contar)
pgcli pg_dump -Fc --no-owner --no-privileges "${URL%%\?*}" -f "$BACKUP_DIR/$NOME.partial"      # grava num arquivo PARCIAL…
pgcli pg_restore --list "$BACKUP_DIR/$NOME.partial" >/dev/null                                # …confirma que o formato é legível…
DEPOIS=$(contar)
paste -d' ' <(echo "$ANTES") <(echo "$DEPOIS" | awk '{print $2}') > "$BACKUP_DIR/$NOME.counts"   # tabela antes depois
mv "$BACKUP_DIR/$NOME.partial" "$BACKUP_DIR/$NOME"                                                         # …e só então o nome definitivo (backup incompleto nunca parece completo)
( cd "$BACKUP_DIR" && sha256sum "$NOME" > "$NOME.sha256" )
if [ -n "${BACKUP_S3_URI:-}" ]; then
  aws s3 cp "$BACKUP_DIR/$NOME" "$BACKUP_S3_URI/$NOME" --sse AES256 --only-show-errors
  aws s3 cp "$BACKUP_DIR/$NOME.sha256" "$BACKUP_S3_URI/$NOME.sha256" --sse AES256 --only-show-errors
fi
# retenção: mantém os N mais recentes (os nomes têm data UTC, então a ordem alfabética é a cronológica)
# shellcheck disable=SC2012
ls -1 "$BACKUP_DIR"/minishop-*.dump 2>/dev/null | sort | head -n -"$MANTER" | while read -r velho; do rm -f "$velho" "$velho.sha256" "$velho.counts"; done
TAM=$(stat -c %s "$BACKUP_DIR/$NOME")
printf '{"event":"backup_ok","file":"%s","bytes":%s,"seconds":%s,"kept":%s,"s3":"%s"}\n' "$NOME" "$TAM" "$(( $(date +%s) - INI ))" \
  "$(ls -1 "$BACKUP_DIR"/minishop-*.dump | wc -l)" "${BACKUP_S3_URI:-no}"
