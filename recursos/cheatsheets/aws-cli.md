# Cheatsheet: AWS CLI (módulo 13)

> 💸 Quase tudo que **cria** gera custo. Antes: `aws sts get-caller-identity`, confira a região e `env | grep AWS_` (uma `AWS_ENDPOINT_URL` esquecida manda os comandos para o simulador).

```bash
aws --version · aws configure sso · aws login        # credenciais temporárias (evite chaves permanentes)
aws sts get-caller-identity --query '[Account,Arn]' --output text
aws configure get region · export AWS_PAGER=""
export AWS_ENDPOINT_URL=http://127.0.0.1:5055        # SÓ para o simulador moto (AWS_ACCESS_KEY_ID/SECRET falsas)
```
## Padrões úteis
`--query '...JMESPath...'` · `--output text|json|table` · `--filters Name=tag:Project,Values=minishop-curso` · `aws <serviço> wait <condição>` · `--dry-run` (EC2) · JSON completo em `--tag-specifications`.

## Por serviço (o que o curso usa)
```bash
# S3
aws s3api create-bucket --bucket B --create-bucket-configuration LocationConstraint=sa-east-1
aws s3api put-public-access-block --bucket B --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
aws s3 ls s3://B/ · aws s3 cp arquivo s3://B/products/ · aws s3api list-object-versions --bucket B
uv run python scripts/aws/empty_bucket.py B && aws s3 rb s3://B        # rb --force NÃO apaga versões
# IAM
aws iam create-role --role-name R --assume-role-policy-document file://trust.json
aws iam put-role-policy --role-name R --policy-name app --policy-document file://politica.json
aws iam create-instance-profile --instance-profile-name R && aws iam add-role-to-instance-profile --instance-profile-name R --role-name R
# EC2 / rede
aws ec2 describe-vpcs --filters Name=isDefault,Values=true
aws ec2 create-security-group --group-name N --description D --vpc-id V
aws ec2 authorize-security-group-ingress --group-id SG --protocol tcp --port 5432 --source-group SG_WEB
aws ec2 run-instances --image-id AMI --instance-type t3.micro --metadata-options HttpTokens=required ...
aws ec2 terminate-instances --instance-ids I && aws ec2 wait instance-terminated --instance-ids I
aws ec2 describe-addresses · aws ec2 release-address --allocation-id A
# RDS
aws rds create-db-instance ... --no-publicly-accessible --storage-encrypted --no-multi-az
aws rds wait db-instance-available --db-instance-identifier D
aws rds delete-db-instance --db-instance-identifier D --skip-final-snapshot --delete-automated-backups
# Parameter Store / Secrets Manager
aws ssm put-parameter --name /minishop/X --type SecureString --value V [--overwrite]
aws ssm get-parameters-by-path --path /minishop --with-decryption
aws secretsmanager create-secret --name N --secret-string '{"k":"v"}'
# Session Manager (sem SSH)
aws ssm start-session --target I
aws ssm send-command --instance-ids I --document-name AWS-RunShellScript --parameters 'commands=["docker ps"]'
# Logs e alarmes
aws logs create-log-group --log-group-name /minishop/app && aws logs put-retention-policy --log-group-name /minishop/app --retention-in-days 7
aws logs tail /minishop/app --follow --since 10m
aws cloudwatch put-metric-alarm --alarm-name A --namespace AWS/EC2 --metric-name CPUUtilization ...
# Orçamento
bash scripts/aws/budget.sh voce@exemplo.com 10
```
## Destruir e conferir (scripts do projeto)
```bash
CONFIRMO=sim bash scripts/aws/destroy.sh        # ordem: EC2 → RDS → SGs → bucket → ECR/logs/parâmetros → IAM → EIP/EBS → conferência
bash scripts/aws/verify_clean.sh                # sai com 1 se sobrar algo (só na região atual!)
```
No dia seguinte: painel de custos por **serviço** e por **região**.
