# Mapa do módulo 13 (material do curso)

Laboratório do módulo 13: o projeto do módulo 12 com **mídia no S3**, **TLS no banco** e os **scripts da AWS**.

> ⚠️ **Verificação honesta.** Não houve conta AWS no laboratório. Os scripts foram executados contra o **moto** (simulador de AWS) e o pacote de deploy foi executado com **Docker Compose local**, usando um PostgreSQL de container no lugar do RDS e o moto no lugar do S3. Isto valida a **sintaxe da CLI, a ordem, a idempotência e a lógica**, **não** o comportamento real da AWS (preços, tempos, limites do plano, permissões de verdade). Veja cada aula.

| Onde | Aula |
|---|---|
| `scripts/aws/budget.sh` | 13.01 |
| `scripts/aws/policies/*.json*`, `scripts/aws/lint_policy.py` | 13.03 |
| `scripts/aws/provision.sh` (passos 5 e 8), `deploy/user-data.sh.tpl`, `scripts/aws/render_user_data.py` | 13.04 |
| `scripts/aws/provision.sh` (passo 6), `config/envconf.py` (`?sslmode=`), `tests/test_envconf.py` | 13.05 |
| `config/settings.py` (`STORAGES`), `apps/catalog/{models,serializers,api}.py` (`image`), `tests/test_midia_s3.py` | 13.06 |
| `deploy/compose.prod.yaml`, `deploy/nginx.conf`, `scripts/aws/deploy.sh` | 13.07 |
| `deploy/compose.awslogs.yaml`, `scripts/aws/destroy.sh`, `scripts/aws/verify_clean.sh` | 13.08 |

Para repetir o teste contra o simulador: `uv run moto_server -p 5055` (com `MOTO_IAM_LOAD_MANAGED_POLICIES=true`) e, em outro terminal,
`AWS_ENDPOINT_URL=http://127.0.0.1:5055 AWS_ACCESS_KEY_ID=t AWS_SECRET_ACCESS_KEY=t AWS_DEFAULT_REGION=sa-east-1 CONFIRMO=sim bash scripts/aws/provision.sh`.
Troque as credenciais falsas por reais e **remova `AWS_ENDPOINT_URL`** para usar a AWS de verdade (💸).
