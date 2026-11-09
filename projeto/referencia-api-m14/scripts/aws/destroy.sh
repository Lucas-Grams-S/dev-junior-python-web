#!/usr/bin/env bash
# Apaga TUDO o que o provision.sh criou, na ordem inversa (aula 13.08). Idempotente: pode rodar de novo se algo falhar no meio.
# Uso: bash scripts/aws/destroy.sh     |   CONFIRMO=sim bash scripts/aws/destroy.sh
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 1
source scripts/aws/config.sh

echo "Vai APAGAR na conta $(aws sts get-caller-identity --query Account --output text) ($AWS_DEFAULT_REGION): EC2, RDS (SEM snapshot final), bucket $BUCKET (com os arquivos), ECR, logs, parâmetros, papel IAM e security groups."
if [ "${CONFIRMO:-}" != "sim" ]; then read -r -p "Digite 'sim' para apagar: " r; [ "$r" = "sim" ] || exit 1; fi
passo() { printf '\n== %s\n' "$*"; }
tentar() { "$@" >/dev/null 2>&1 && echo "   ok: $*" | cut -c1-110 || echo "   (nada a fazer / já apagado): $*" | cut -c1-110; }

passo "1/8 EC2"
IDS=$(aws ec2 describe-instances --filters "Name=tag:Project,Values=$PROJECT_TAG" Name=instance-state-name,Values=pending,running,stopping,stopped \
  --query 'Reservations[].Instances[].InstanceId' --output text)
if [ -n "$IDS" ]; then
  # shellcheck disable=SC2086
  aws ec2 terminate-instances --instance-ids $IDS >/dev/null && aws ec2 wait instance-terminated --instance-ids $IDS && echo "   terminada(s): $IDS"
fi

passo "2/8 RDS (sem snapshot final; apaga também os backups automáticos)"
if aws rds describe-db-instances --db-instance-identifier "$DB_ID" >/dev/null 2>&1; then
  aws rds delete-db-instance --db-instance-identifier "$DB_ID" --skip-final-snapshot --delete-automated-backups >/dev/null
  aws rds wait db-instance-deleted --db-instance-identifier "$DB_ID" && echo "   banco apagado"
fi
tentar aws rds delete-db-subnet-group --db-subnet-group-name "$NAME-db"

passo "3/8 Security groups (o do banco primeiro: ele referencia o do web)"
for g in "$NAME-db" "$NAME-web"; do
  GID=$(aws ec2 describe-security-groups --filters Name=group-name,Values="$g" "Name=tag:Project,Values=$PROJECT_TAG" --query 'SecurityGroups[0].GroupId' --output text 2>/dev/null)
  [ -n "$GID" ] && [ "$GID" != "None" ] && tentar aws ec2 delete-security-group --group-id "$GID"
done

passo "4/8 Bucket S3 (esvazia, INCLUSIVE versões e marcadores, e apaga; o rb --force sozinho não apaga versões)"
uv run python scripts/aws/empty_bucket.py "$BUCKET"
tentar aws s3 rb "s3://$BUCKET" --force

passo "5/8 ECR, logs e parâmetros"
tentar aws ecr delete-repository --repository-name "$NAME" --force
tentar aws logs delete-log-group --log-group-name "/$NAME/app"
NOMES=$(aws ssm get-parameters-by-path --path "/$NAME" --query 'Parameters[].Name' --output text 2>/dev/null)
# shellcheck disable=SC2086
[ -n "$NOMES" ] && tentar aws ssm delete-parameters --names $NOMES

passo "6/8 IAM (papel, política embutida, instance profile)"
tentar aws iam remove-role-from-instance-profile --instance-profile-name "$NAME-ec2" --role-name "$NAME-ec2"
tentar aws iam delete-instance-profile --instance-profile-name "$NAME-ec2"
tentar aws iam delete-role-policy --role-name "$NAME-ec2" --policy-name app
tentar aws iam detach-role-policy --role-name "$NAME-ec2" --policy-arn arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore
tentar aws iam delete-role --role-name "$NAME-ec2"

passo "7/8 IPs elásticos, volumes EBS soltos e snapshots manuais do projeto (não deveria haver; IP elástico sem uso é COBRADO)"
for a in $(aws ec2 describe-addresses --filters "Name=tag:Project,Values=$PROJECT_TAG" --query 'Addresses[].AllocationId' --output text); do tentar aws ec2 release-address --allocation-id "$a"; done
for v in $(aws ec2 describe-volumes --filters "Name=tag:Project,Values=$PROJECT_TAG" --query 'Volumes[].VolumeId' --output text); do tentar aws ec2 delete-volume --volume-id "$v"; done
for s in $(aws ec2 describe-snapshots --owner-ids self --filters "Name=tag:Project,Values=$PROJECT_TAG" --query 'Snapshots[].SnapshotId' --output text); do tentar aws ec2 delete-snapshot --snapshot-id "$s"; done

passo "8/8 Conferência"
bash scripts/aws/verify_clean.sh
