#!/usr/bin/env bash
# Publica a imagem no ECR e manda a instância atualizar (sem SSH: AWS Systems Manager Run Command).
# Uso: bash scripts/aws/deploy.sh [TAG]     (TAG padrão: sha curto do commit atual)
set -euo pipefail
cd "$(dirname "$0")/../.." || exit 1
source scripts/aws/config.sh
TAG="${1:-sha-$(git rev-parse --short HEAD)}"
ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
REGISTRY="$ACCOUNT.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com"

echo "== construir (linux/amd64, o mesmo tipo da EC2 t3) e enviar $REGISTRY/$NAME:$TAG"
docker build --platform linux/amd64 -t "$REGISTRY/$NAME:$TAG" .
aws ecr get-login-password | docker login --username AWS --password-stdin "$REGISTRY"
docker push "$REGISTRY/$NAME:$TAG"

echo "== atualizar a instância"
INSTANCE_ID=$(aws ec2 describe-instances --filters "Name=tag:Project,Values=$PROJECT_TAG" Name=instance-state-name,Values=running \
  --query 'Reservations[0].Instances[0].InstanceId' --output text)
CMD_ID=$(aws ssm send-command --instance-ids "$INSTANCE_ID" --document-name AWS-RunShellScript \
  --parameters "commands=[\"/opt/minishop/update.sh $TAG\"]" --query Command.CommandId --output text)
aws ssm wait command-executed --command-id "$CMD_ID" --instance-id "$INSTANCE_ID" || true
aws ssm get-command-invocation --command-id "$CMD_ID" --instance-id "$INSTANCE_ID" --query '[Status,StandardErrorContent]' --output text
