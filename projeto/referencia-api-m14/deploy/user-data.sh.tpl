#!/bin/bash
# user-data da EC2 (roda UMA vez, no primeiro boot, como root). Log: /var/log/minishop-user-data.log
set -euxo pipefail
exec > >(tee /var/log/minishop-user-data.log) 2>&1

dnf install -y docker
systemctl enable --now docker

# Plugin do Compose, versão fixa e checksum conferido (o mesmo Compose v5.6.1 usado no módulo 11)
mkdir -p /usr/local/lib/docker/cli-plugins
curl -fsSL -o /usr/local/lib/docker/cli-plugins/docker-compose \
  https://github.com/docker/compose/releases/download/v5.6.1/docker-compose-linux-x86_64
echo "47737f4236e6d3ccea7291995203f8f018058783b4c3a9469119811a0b5db8c0  /usr/local/lib/docker/cli-plugins/docker-compose" | sha256sum -c -
chmod +x /usr/local/lib/docker/cli-plugins/docker-compose

mkdir -p /opt/minishop && cd /opt/minishop

cat > compose.prod.yaml <<'EOF_COMPOSE'
__COMPOSE__
EOF_COMPOSE

cat > compose.awslogs.yaml <<'EOF_AWSLOGS'
__AWSLOGS__
EOF_AWSLOGS

cat > nginx.conf <<'EOF_NGINX'
__NGINX__
EOF_NGINX

# Script de atualização: login no ECR, baixa a imagem da tag pedida e recria o que mudou
cat > update.sh <<'EOF_UPDATE'
#!/bin/bash
set -euo pipefail
cd /opt/minishop
TAG="${1:?uso: update.sh TAG}"
TOKEN=$(curl -sX PUT http://169.254.169.254/latest/api/token -H "X-aws-ec2-metadata-token-ttl-seconds: 300")
REGION=$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/placement/region)
ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
REGISTRY="$ACCOUNT.dkr.ecr.$REGION.amazonaws.com"
aws ecr get-login-password --region "$REGION" | docker login --username AWS --password-stdin "$REGISTRY"
printf "IMAGE=%s/minishop:%s\nRELEASE=%s\n" "$REGISTRY" "$TAG" "$TAG" > image.env
FILES="-f compose.prod.yaml"
[ -f use-awslogs ] && FILES="$FILES -f compose.awslogs.yaml"      # opt-in: touch /opt/minishop/use-awslogs (aula 13.08)
# shellcheck disable=SC2086
docker compose $FILES --env-file image.env pull
# shellcheck disable=SC2086
docker compose $FILES --env-file image.env up -d --remove-orphans
docker image prune -f
EOF_UPDATE
chmod +x update.sh

# Configuração: segredos e parâmetros vêm do Parameter Store (nada de segredo neste script)
TOKEN=$(curl -sX PUT http://169.254.169.254/latest/api/token -H "X-aws-ec2-metadata-token-ttl-seconds: 300")
IMDS() { curl -s -H "X-aws-ec2-metadata-token: $TOKEN" "http://169.254.169.254/latest/meta-data/$1"; }
REGION=$(IMDS placement/region)
PUBLIC_IP=$(IMDS public-ipv4)
umask 077
aws ssm get-parameters-by-path --path /minishop --with-decryption --region "$REGION" \
  --query 'Parameters[].[Name,Value]' --output text | grep -v '^/minishop/DB_PASSWORD' | while IFS=$'\t' read -r nome valor; do
  echo "${nome##*/}=$valor"
done > .env
cat >> .env <<EOF_ENV
DEBUG=0
ALLOWED_HOSTS=$PUBLIC_IP,localhost
SECURE_SSL_REDIRECT=0
SECURE_HSTS_SECONDS=0
NUM_PROXIES=1
CELERY_BROKER_URL=redis://redis:6379/0
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_CACHE_URL=redis://redis:6379/1
EMAIL_OUTBOX_FILE=/data/outbox.jsonl
AWS_REGION=$REGION
EOF_ENV
chmod 600 .env

# Primeira tentativa: a imagem só existe depois do deploy.sh (ECR vazio no início é normal)
./update.sh latest || echo "Imagem ainda não publicada no ECR: rode scripts/aws/deploy.sh"
