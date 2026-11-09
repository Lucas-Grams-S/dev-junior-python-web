# Projeto de referência: MiniShop até o módulo 9 (segurança)

É o **laboratório usado para executar e verificar** as aulas do módulo 9. Contém tudo do módulo 8 e acrescenta: Argon2id e validadores de senha, cabeçalhos de segurança (CSP e outros), rotas de demonstração/documentação sob controle, eventos de segurança, matriz de autorização, rotinas da LGPD (exportar e anonimizar) e o relatório `docs/seguranca.md`.

> ⚠️ **Uso responsável.** Tudo aqui é para testar **o seu próprio ambiente local**. `seclab/consultas.py` contém um anti-padrão **de propósito** (para o `ruff`/`bandit` apontarem); ele não é roteado. O `seed` cria usuários com senha de desenvolvimento e **recusa rodar fora de `DEBUG=1`**.

## Como rodar
```bash
uv sync
DEBUG=1 uv run python manage.py migrate
DEBUG=1 uv run python manage.py seed        # usuários: gerente, estoquista, cliente (senha dev-somente-local-123)
uv run pytest -q                            # 235 passed, 1 skipped em SQLite
uv run lint-imports                         # 3 contratos
uv run ruff check --select S --ignore S101,S311 --exclude tests,seclab,migrations,legado apps config
uv run bandit -r apps config -q --exclude "apps/*/migrations"
uv export --no-hashes --no-emit-project -o /tmp/req.txt && uv run pip-audit -r /tmp/req.txt --no-deps --disable-pip
```
Em PostgreSQL (paridade): `DEBUG=1 DATABASE_URL=postgres://usuario:senha@127.0.0.1:5498/postgres uv run pytest -q` → 232 passed, 4 skipped (o usuário precisa poder criar o banco de testes).

## Mapa (módulo 9)
| Onde | Aula |
|---|---|
| `scripts/m9/auditoria.py` (sondagens contra o OWASP Top 10:2025), `docs/seguranca.md` | 9.01 |
| `seclab/consultas.py`, `scripts/m9/xss_escape.py`, `scripts/m9/ferramentas.sh`, `tests/test_sqli_defesa.py`, `tests/test_pontos_perigosos.py` | 9.02 |
| `scripts/m9/csrf_sessao_jwt.py`, `tests/test_sessao_csrf_jwt.py` | 9.03 |
| `scripts/m9/hash_bench.py`, `timing_login.py`, `config/settings.py` (senhas), `tests/test_senhas.py` | 9.04 |
| `tests/test_matriz_autorizacao.py`, `config/errors.py` (`ConflictError`) | 9.05 |
| `config/security_headers.py`, `apps/accounts/receivers.py`, `scripts/m9/limite_workers.sh`, `tests/test_endurecimento.py` | 9.06 |
| `scripts/m9/gerar_certificados.sh`, `https_demo.sh`, `tls_versoes.py`, `roles.sql`, `privilegios.py`, `apps/accounts/lgpd.py`, `tests/test_lgpd.py`, `docs/privacidade.md` | 9.07 |
| `scripts/m9/saidas/` | as saídas reais coladas nas aulas |

Os scripts assumem `LAB` apontando para a raiz do projeto (por exemplo `DEBUG=0 SECRET_KEY=... ALLOWED_HOSTS=testserver SECURE_SSL_REDIRECT=0 ORDER_EMAIL_MODE=off LAB=$PWD uv run python scripts/m9/auditoria.py`). Os de rede (`https_demo.sh`, `limite_workers.sh`, `privilegios.py`) precisam de portas livres, `openssl`, Redis (6391) e PostgreSQL (5498) de laboratório, como descrito nas aulas.
