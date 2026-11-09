#!/usr/bin/env bash
# Confere que NADA do projeto sobrou (aula 13.08). Sai com 1 se achar qualquer recurso. Roda em todas as regiões que você usou? Não:
# só em $AWS_DEFAULT_REGION. Se você criou algo em outra região por engano, rode com AWS_DEFAULT_REGION=outra.
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 1
source scripts/aws/config.sh
sobrou=0
achou() { printf '  SOBROU  %-14s %s\n' "$1" "$2"; sobrou=1; }
limpo() { printf '  limpo   %s\n' "$1"; }
checa() { local rotulo="$1" saida="$2"; if [ -n "$saida" ] && [ "$saida" != "None" ]; then achou "$rotulo" "$saida"; else limpo "$rotulo"; fi; }

checa "EC2"        "$(aws ec2 describe-instances --filters "Name=tag:Project,Values=$PROJECT_TAG" Name=instance-state-name,Values=pending,running,stopping,stopped,shutting-down --query 'Reservations[].Instances[].InstanceId' --output text)"
checa "EBS"        "$(aws ec2 describe-volumes --filters "Name=tag:Project,Values=$PROJECT_TAG" --query 'Volumes[].VolumeId' --output text)"
checa "Snapshots"  "$(aws ec2 describe-snapshots --owner-ids self --filters "Name=tag:Project,Values=$PROJECT_TAG" --query 'Snapshots[].SnapshotId' --output text)"
checa "IP elástico" "$(aws ec2 describe-addresses --filters "Name=tag:Project,Values=$PROJECT_TAG" --query 'Addresses[].PublicIp' --output text)"
checa "Sec. groups" "$(aws ec2 describe-security-groups --filters "Name=tag:Project,Values=$PROJECT_TAG" --query 'SecurityGroups[].GroupId' --output text)"
checa "RDS"        "$(aws rds describe-db-instances --query "DBInstances[?DBInstanceIdentifier=='$DB_ID'].DBInstanceIdentifier" --output text 2>/dev/null)"
checa "RDS snapshots" "$(aws rds describe-db-snapshots --snapshot-type manual --query "DBSnapshots[?DBInstanceIdentifier=='$DB_ID'].DBSnapshotIdentifier" --output text 2>/dev/null)"
checa "S3"         "$(aws s3api list-buckets --query "Buckets[?Name=='$BUCKET'].Name" --output text)"
checa "ECR"        "$(aws ecr describe-repositories --query "repositories[?repositoryName=='$NAME'].repositoryName" --output text 2>/dev/null)"
checa "Logs"       "$(aws logs describe-log-groups --log-group-name-prefix "/$NAME" --query 'logGroups[].logGroupName' --output text)"
checa "Parâmetros" "$(aws ssm get-parameters-by-path --path "/$NAME" --query 'Parameters[].Name' --output text 2>/dev/null)"
checa "IAM papel"  "$(aws iam list-roles --query "Roles[?RoleName=='$NAME-ec2'].RoleName" --output text)"
checa "IAM profile" "$(aws iam list-instance-profiles --query "InstanceProfiles[?InstanceProfileName=='$NAME-ec2'].InstanceProfileName" --output text)"
# rede de segurança: qualquer outra coisa com a tag (a API de tags enxerga vários serviços de uma vez)
# instâncias TERMINADAS continuam listadas por ~1 hora e não custam nada: não contam como "sobra"
TERMINADAS=$(aws ec2 describe-instances --filters "Name=tag:Project,Values=$PROJECT_TAG" Name=instance-state-name,Values=terminated --query 'Reservations[].Instances[].InstanceId' --output text | tr '\t' '|')
TAGS=$(aws resourcegroupstaggingapi get-resources --tag-filters "Key=Project,Values=$PROJECT_TAG" --query 'ResourceTagMappingList[].ResourceARN' --output text 2>/dev/null | tr '\t' '\n')
[ -n "$TERMINADAS" ] && TAGS=$(echo "$TAGS" | grep -Ev "instance/($TERMINADAS)$" || true)
checa "Tag API"    "$TAGS"

if [ "$sobrou" = 0 ]; then echo "TUDO LIMPO (nesta região: $AWS_DEFAULT_REGION). Confira também o painel de Billing amanhã."; else echo "ATENÇÃO: ainda há recursos."; fi
exit $sobrou
