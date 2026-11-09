# shellcheck shell=bash
# Fazer `source`. Define pgcli(): usa o cliente PostgreSQL local se existir; senão, um contêiner `postgres:18` (só o cliente; o servidor é outro).
# Variáveis: PG_IMAGE (padrão postgres:18), PG_DOCKER_ARGS (ex.: --network host ou --network minha-rede), BACKUP_DIR (montado no contêiner).
pgcli() {
  local prog="$1"; shift
  if command -v "$prog" >/dev/null 2>&1 && [ -z "${PG_FORCE_DOCKER:-}" ]; then "$prog" "$@"; return; fi
  # shellcheck disable=SC2086
  docker run --rm -i -u "$(id -u):$(id -g)" ${PG_DOCKER_ARGS:---network host} -v "${BACKUP_DIR:-$PWD}:${BACKUP_DIR:-$PWD}" -w "${BACKUP_DIR:-$PWD}" "${PG_IMAGE:-postgres:18}" "$prog" "$@"
}
# pgurl_servidor URL → URL sem o nome do banco e sem query (postgres://u:p@h:5432); pgurl_banco URL → só o nome do banco
pgurl_servidor() { local b="${1%%\?*}"; echo "${b%/*}"; }
pgurl_banco() { local b="${1%%\?*}"; echo "${b##*/}"; }
