#!/usr/bin/env bash
# Cria na AWS tudo o que o MiniShop usa (aula 13). 💸 GERA CUSTO: leia a aula 13.01 e o roteiro de destruição ANTES de rodar.
# Uso:  bash scripts/aws/provision.sh            (pede confirmação)    |    CONFIRMO=sim bash scripts/aws/provision.sh
# Para testar a LÓGICA sem conta AWS: AWS_ENDPOINT_URL=http://127.0.0.1:5055 (moto) com credenciais falsas.
set -euo pipefail
cd "$(dirname "$0")/../.." || exit 1
source scripts/aws/config.sh

echo "Conta: $(aws sts get-caller-identity --query Account --output text)   Região: $AWS_DEFAULT_REGION   Tag: Project=$PROJECT_TAG"
echo "Vai criar: S3, ECR, log group, parâmetros SSM, papel IAM, 2 security groups, RDS ($DB_CLASS) e EC2 ($INSTANCE_TYPE)."
if [ "${CONFIRMO:-}" != "sim" ]; then read -r -p "💸 Isso pode gerar cobrança. Digite 'sim' para continuar: " r; [ "$r" = "sim" ] || exit 1; fi
passo() { printf '\n== %s\n' "$*"; }
senha() { python3 -c 'import secrets; print(secrets.token_urlsafe(24))'; }

passo "1/9 Bucket S3 privado (bloqueio de acesso público, criptografia, tags)"
aws s3api create-bucket --bucket "$BUCKET" --create-bucket-configuration LocationConstraint="$AWS_DEFAULT_REGION" >/dev/null
aws s3api put-public-access-block --bucket "$BUCKET" --public-access-block-configuration \
  BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
aws s3api put-bucket-encryption --bucket "$BUCKET" --server-side-encryption-configuration \
  '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}'
aws s3api put-bucket-tagging --bucket "$BUCKET" --tagging "{\"TagSet\":$TAGS_SPEC_JSON}"

passo "2/9 Repositório de imagens (ECR) e grupo de logs (CloudWatch, retenção de 7 dias)"
aws ecr create-repository --repository-name "$NAME" --image-scanning-configuration scanOnPush=true --tags $TAGS_KV >/dev/null
aws logs create-log-group --log-group-name "/$NAME/app" --tags "Project=$PROJECT_TAG"
aws logs put-retention-policy --log-group-name "/$NAME/app" --retention-in-days 7

passo "3/9 Segredos no Parameter Store (SecureString)"
DB_PASSWORD="$(senha)"
aws ssm put-parameter --name "/$NAME/SECRET_KEY"  --type SecureString --value "$(senha)$(senha)" --tags $TAGS_KV >/dev/null
aws ssm put-parameter --name "/$NAME/DB_PASSWORD" --type SecureString --value "$DB_PASSWORD" --tags $TAGS_KV >/dev/null
# configuração não secreta também vai para o Parameter Store (tipo String): a instância lê tudo de um só lugar
aws ssm put-parameter --name "/$NAME/AWS_STORAGE_BUCKET_NAME" --type String --value "$BUCKET" --tags $TAGS_KV >/dev/null
aws ssm put-parameter --name "/$NAME/AWS_S3_REGION_NAME" --type String --value "$AWS_DEFAULT_REGION" --tags $TAGS_KV >/dev/null

passo "4/9 Papel IAM da instância (menor privilégio) e instance profile"
aws iam create-role --role-name "$NAME-ec2" --assume-role-policy-document file://scripts/aws/policies/ec2-trust.json --tags $TAGS_KV >/dev/null
sed "s/__BUCKET__/$BUCKET/g" scripts/aws/policies/app-policy.json.tpl > /tmp/minishop-app-policy.json
python3 scripts/aws/lint_policy.py /tmp/minishop-app-policy.json
aws iam put-role-policy --role-name "$NAME-ec2" --policy-name app --policy-document file:///tmp/minishop-app-policy.json
aws iam attach-role-policy --role-name "$NAME-ec2" --policy-arn arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore   # acesso por Session Manager, sem SSH
aws iam create-instance-profile --instance-profile-name "$NAME-ec2" --tags $TAGS_KV >/dev/null
aws iam add-role-to-instance-profile --instance-profile-name "$NAME-ec2" --role-name "$NAME-ec2"

passo "5/9 Rede: VPC padrão e security groups (web: 80 aberto, sem SSH; banco: 5432 SÓ a partir do web)"
VPC_ID=$(aws ec2 describe-vpcs --filters Name=isDefault,Values=true --query 'Vpcs[0].VpcId' --output text)
SG_WEB=$(aws ec2 create-security-group --group-name "$NAME-web" --description "MiniShop web" --vpc-id "$VPC_ID" \
  --tag-specifications "[{\"ResourceType\":\"security-group\",\"Tags\":$TAGS_SPEC_JSON}]" --query GroupId --output text)
SG_DB=$(aws ec2 create-security-group --group-name "$NAME-db" --description "MiniShop banco" --vpc-id "$VPC_ID" \
  --tag-specifications "[{\"ResourceType\":\"security-group\",\"Tags\":$TAGS_SPEC_JSON}]" --query GroupId --output text)
aws ec2 authorize-security-group-ingress --group-id "$SG_WEB" --protocol tcp --port 80 --cidr 0.0.0.0/0 >/dev/null
aws ec2 authorize-security-group-ingress --group-id "$SG_DB" --protocol tcp --port 5432 --source-group "$SG_WEB" >/dev/null
echo "VPC=$VPC_ID  SG_WEB=$SG_WEB  SG_DB=$SG_DB"

passo "6/9 💸 Banco RDS PostgreSQL ($DB_CLASS, 1 AZ, 20 GB, privado, criptografado). Leva vários minutos."
SUBNETS=$(aws ec2 describe-subnets --filters Name=vpc-id,Values="$VPC_ID" --query 'Subnets[].SubnetId' --output text)
# shellcheck disable=SC2086
aws rds create-db-subnet-group --db-subnet-group-name "$NAME-db" --db-subnet-group-description "MiniShop" --subnet-ids $SUBNETS --tags $TAGS_KV >/dev/null
VERSAO=(); [ -n "$DB_ENGINE_VERSION" ] && VERSAO=(--engine-version "$DB_ENGINE_VERSION")
aws rds create-db-instance --db-instance-identifier "$DB_ID" --engine postgres "${VERSAO[@]}" \
  --db-instance-class "$DB_CLASS" --allocated-storage 20 --storage-type gp3 --storage-encrypted \
  --master-username minishop --master-user-password "$DB_PASSWORD" --db-name minishop \
  --db-subnet-group-name "$NAME-db" --vpc-security-group-ids "$SG_DB" --no-publicly-accessible --no-multi-az \
  --backup-retention-period 1 --no-deletion-protection --tags $TAGS_KV >/dev/null
aws rds wait db-instance-available --db-instance-identifier "$DB_ID"
DB_HOST=$(aws rds describe-db-instances --db-instance-identifier "$DB_ID" --query 'DBInstances[0].Endpoint.Address' --output text)
aws ssm put-parameter --name "/$NAME/DATABASE_URL" --type SecureString --tags $TAGS_KV \
  --value "postgres://minishop:${DB_PASSWORD}@${DB_HOST}:5432/minishop" >/dev/null
echo "Endpoint do banco: $DB_HOST"

passo "7/9 user-data (instala Docker e sobe o Compose no primeiro boot)"
python3 scripts/aws/render_user_data.py > /tmp/minishop-user-data.sh
echo "user-data: $(wc -c < /tmp/minishop-user-data.sh) bytes (limite da AWS: 16384)"

passo "8/9 💸 Instância EC2 ($INSTANCE_TYPE, Amazon Linux 2023, IMDSv2 obrigatório, disco criptografado)"
AMI=$(aws ssm get-parameter --name /aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64 --query Parameter.Value --output text)
SUBNET_1=$(echo "$SUBNETS" | awk '{print $1}')
INSTANCE_ID=$(aws ec2 run-instances --image-id "$AMI" --instance-type "$INSTANCE_TYPE" --subnet-id "$SUBNET_1" \
  --security-group-ids "$SG_WEB" --iam-instance-profile Name="$NAME-ec2" --associate-public-ip-address \
  --metadata-options HttpTokens=required,HttpEndpoint=enabled \
  --block-device-mappings 'DeviceName=/dev/xvda,Ebs={VolumeSize=12,VolumeType=gp3,Encrypted=true,DeleteOnTermination=true}' \
  --user-data file:///tmp/minishop-user-data.sh \
  --tag-specifications "[{\"ResourceType\":\"instance\",\"Tags\":[{\"Key\":\"Project\",\"Value\":\"$PROJECT_TAG\"},{\"Key\":\"Name\",\"Value\":\"$NAME\"}]},{\"ResourceType\":\"volume\",\"Tags\":$TAGS_SPEC_JSON}]" \
  --query 'Instances[0].InstanceId' --output text)
aws ec2 wait instance-running --instance-ids "$INSTANCE_ID"
IP=$(aws ec2 describe-instances --instance-ids "$INSTANCE_ID" --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)

passo "9/9 Resumo"
cat <<RESUMO
Instância: $INSTANCE_ID   IP público: $IP   (💸 IPv4 público é cobrado por hora)
Bucket:    $BUCKET
Banco:     $DB_HOST
Depois de publicar a imagem no ECR (scripts/aws/deploy.sh), abra  http://$IP/api/docs/  (somente se EXPOSE_DOCS=1)
DESTRUIR:  bash scripts/aws/destroy.sh   e conferir:  bash scripts/aws/verify_clean.sh
RESUMO
