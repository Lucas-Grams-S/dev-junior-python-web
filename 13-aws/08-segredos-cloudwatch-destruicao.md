# 8. Segredos, CloudWatch e como destruir tudo

> ⏱️ ~1h30 · Módulo 13 · Pré-requisitos: [13.01](01-conceitos-conta-mfa-custos.md), [13.03](03-iam.md), [13.07](07-deploy-minishop.md), [9.06 (segredos)](../09-seguranca/06-segredos-dependencias-headers-rate-limit.md)

> ✅ **Verificação.** Executado **contra o `moto`** (simulador): o `provision.sh` completo, a leitura dos parâmetros e a montagem do `.env` (o mesmo trecho do `user-data`), Secrets Manager, grupo de logs com retenção, um alarme de CPU, e o ciclo `destroy.sh` → `verify_clean.sh` **repetido várias vezes**, inclusive com recursos "esquecidos" de propósito (IP elástico solto, volume EBS solto, bucket com versões). Validei também a **configuração do Compose** com o driver `awslogs`. **Não executado (sem conta AWS):** o driver `awslogs` enviando de verdade ao CloudWatch, o Logs Insights, alarmes reais (inclusive de faturamento), o Secrets Manager com rotação, e **a destruição na AWS real**. O `moto` aceita comandos que a AWS recusaria e **não** cobra. Antes de confiar no `destroy.sh` na sua conta, leia o roteiro e rode o `verify_clean.sh` **você mesmo**, no painel e por região. 💸 Esta aula trata justamente de parar a cobrança. Código em [`projeto/referencia-api-m13/`](../projeto/referencia-api-m13/README.md).

## 🎯 Objetivos
- Guardar **segredos** no Parameter Store (e comparar com o Secrets Manager), lê-los pela instância **sem expô-los** e rotacioná-los
- Enviar e consultar **logs no CloudWatch** com retenção definida, e criar um **alarme**
- **Destruir tudo** na ordem certa, **conferir** que nada sobrou e saber o que **continua** existindo depois
- Reconhecer as armadilhas que fazem a conta continuar cobrando
- Fechar o ciclo: criar → usar → destruir → conferir **no mesmo dia**

## 🤔 Por que isso importa
Segredos mal guardados e recursos esquecidos são as duas formas mais comuns de uma conta de estudo virar prejuízo ou incidente. Um júnior que **sabe destruir com segurança** e **prova** que destruiu demonstra mais maturidade do que quem só sabe criar. Em entrevista: "onde ficam as senhas do seu app na nuvem?" e "como você evita custos esquecidos?" são perguntas diretas.

## 💡 Intuição (explicação simples)
Os segredos são **chaves de um cofre**: não ficam coladas na porta (código), nem num bilhete na recepção (variável de ambiente no repositório); ficam num **chaveiro com controle de entrada** (Parameter Store), e quem precisa recebe a chave na hora. Os logs são o **diário de bordo** da loja, guardado num arquivo central com prazo de validade. E a destruição é o **fechamento de caixa**: no fim do dia você desliga tudo, **confere cada porta e cada luz** com uma lista, e só então vai embora. No dia seguinte, confere o extrato.

## 🔬 Como funciona por dentro
**Segredos: Parameter Store × Secrets Manager** (conceitual; confira preços e limites na documentação)
| | **Systems Manager Parameter Store** | **Secrets Manager** |
|---|---|---|
| Para quê | configuração e segredos simples | segredos que precisam de **rotação** e ciclo de vida |
| Tipos | `String`, `StringList`, `SecureString` (cifrado com KMS) | JSON/texto cifrado |
| Rotação automática | não nativa | **sim** (integração pronta com RDS) |
| Custo | camada padrão gratuita (parâmetros "standard") | cobrança por segredo/mês + chamadas |
| Hierarquia | caminhos (`/minishop/DATABASE_URL`) | nomes/ARNs |
| Controle de acesso | IAM por caminho (`parameter/minishop/*`) | IAM por segredo |
No curso: **Parameter Store**, pela simplicidade e custo; a rotação da senha do RDS (Secrets Manager) é a evolução natural. **O que vira parâmetro** (`/minishop/...`): segredos (`SECRET_KEY`, `DB_PASSWORD`, `DATABASE_URL`: `SecureString`) e configuração (`AWS_STORAGE_BUCKET_NAME`, `AWS_S3_REGION_NAME`: `String`). **O que não:** nada de segredo no `user-data` (ele é legível pelos metadados da instância e pelo console), no Git, na imagem ou no Compose. A instância lê tudo com o papel IAM (`ssm:GetParametersByPath` em `parameter/minishop/*`) **no primeiro boot** e grava o `.env` com permissão `600`.

**CloudWatch Logs.** Hierarquia: **grupo de logs** (`/minishop/app`) → **fluxos** (*log streams*: um por contêiner/instância) → **eventos**. Pontos de atenção: (1) a **retenção** vem **ilimitada por padrão**: defina (7 dias no curso), senão paga para guardar logs para sempre; (2) cobra por **ingestão** (GB enviado) e por **armazenamento**; (3) o **Logs Insights** consulta os eventos com uma linguagem própria (cobra por dado analisado). O Docker envia direto, com o driver `awslogs`, que usa as credenciais do papel da instância. **Logs sem segredo e sem dado pessoal** (módulo 9); aqui lembre do token JWT na URL do WebSocket (o Nginx do módulo 11 e o `nginx.conf` do deploy já registram só `$uri`).

**Métricas e alarmes.** O CloudWatch coleta métricas básicas da EC2 (CPU, rede, disco de instância; **memória não vem por padrão**: exige o agente do CloudWatch) e do RDS. Um **alarme** observa uma métrica e muda de estado (`OK`/`ALARM`) acionando uma ação (e-mail via SNS). Alarmes **custam** por unidade. O alarme que mais salva a fatura é o **de faturamento/orçamento** (aula 01).

**Destruir de verdade: a ordem importa.** Recursos têm **dependências**: não se apaga um Security Group usado por uma instância; não se apaga um papel com política anexada; não se apaga um bucket com versões. A ordem do `destroy.sh` é a inversa da criação: **1** EC2 (esperar `terminated`) → **2** RDS (esperar `deleted`) e seu grupo de sub-redes → **3** Security Groups (banco antes do web) → **4** bucket (esvaziar *inclusive versões*) → **5** ECR, logs, parâmetros → **6** IAM (tirar o papel do *instance profile*, apagar o profile, apagar a política embutida, desanexar a gerenciada, apagar o papel) → **7** IP elástico, volumes e snapshots soltos → **8** conferência. O script é **idempotente** (rodar de novo não quebra) e **só toca** em recursos com a tag `Project=minishop-curso` ou com o nome exato do projeto.

**O que a conferência cobre e o que NÃO cobre.** O `verify_clean.sh` lista, **na região configurada**, EC2, EBS, snapshots, IPs elásticos, SGs, RDS e snapshots manuais, bucket, ECR, logs, parâmetros, IAM e (como rede de segurança) tudo que a API de tags enxerga. **Não cobre:** outras regiões, recursos sem tag criados à mão no console, o **provedor OIDC e o papel de deploy** (criados manualmente na aula 07), o **orçamento** e o **monitor de anomalias** (de propósito: são grátis e você quer mantê-los), nem o **faturamento**, que só o painel mostra (e com atraso).

## 🛠️ Exemplo prático
**1. Segredos: criar, ler, rotacionar** (passo 3 do `provision.sh` e o trecho do `user-data`; no `moto`):
```bash
aws ssm put-parameter --name /minishop/SECRET_KEY  --type SecureString --value "$(senha)$(senha)" --tags Key=Project,Value=minishop-curso
aws ssm put-parameter --name /minishop/DB_PASSWORD --type SecureString --value "$DB_PASSWORD"      --tags Key=Project,Value=minishop-curso
aws ssm put-parameter --name /minishop/AWS_STORAGE_BUCKET_NAME --type String --value "$BUCKET"     --tags Key=Project,Value=minishop-curso
```
O mesmo trecho que o `user-data` executa na instância, rodado contra o simulador, e o resultado (com os valores mascarados **por mim**):
```bash
umask 077
aws ssm get-parameters-by-path --path /minishop --with-decryption --query 'Parameters[].[Name,Value]' --output text \
  | grep -v '^/minishop/DB_PASSWORD' | while IFS=$'\t' read -r nome valor; do echo "${nome##*/}=$valor"; done > .env
```
```text
-rw-------                                  ← permissões do .env: só o dono lê
AWS_S3_REGION_NAME=sa-east-1
AWS_STORAGE_BUCKET_NAME=minishop-midia-123456789012
DATABASE_URL=postgres://minishop:******@minishop-db.aaaaaaaaaa.sa-east-1.rds.amazonaws.com:5432/minishop
SECRET_KEY=******
grep -c DB_PASSWORD .env  →  0              ← a senha "solta" do banco nem chega ao .env
```
Os nomes dos parâmetros viram **as variáveis de ambiente** do Django (`${nome##*/}` pega o último trecho do caminho). **Ativar TLS no banco** (o passo que a aula 05 deixou manual): reescreva o parâmetro com `sslmode=require` e **reinicie** a aplicação para ela reler:
```bash
URL=$(aws ssm get-parameter --name /minishop/DATABASE_URL --with-decryption --query Parameter.Value --output text)
aws ssm put-parameter --name /minishop/DATABASE_URL --type SecureString --overwrite --value "${URL}?sslmode=require"
```
```text
2                       ← versão do parâmetro (o histórico guarda a anterior: aws ssm get-parameter-history)
postgres://minishop:******@minishop-db...rds.amazonaws.com:5432/minishop?sslmode=require
kms:alias/aws/ssm:postgres://minishop:xAqdCKolNP...   ← SEM --with-decryption o valor vem CIFRADO (formato do simulador)
```
Rotação manual: gere um valor novo, atualize o RDS (`modify-db-instance --master-user-password`) **e** o parâmetro, e reinicie (`update.sh`); com Secrets Manager isso é automatizável. **Quem tem `ssm:GetParameter` com descriptografia tem o segredo**: por isso a política da aplicação restringe a `/minishop/*` (aula 03). O Secrets Manager, no simulador:
```text
$ aws secretsmanager create-secret --name minishop/exemplo --secret-string '{"user":"x","password":"y"}'  → minishop/exemplo
$ aws secretsmanager get-secret-value --secret-id minishop/exemplo --query SecretString --output text      → {"user":"x","password":"y"}
```

**2. Logs com retenção e o driver `awslogs`.**
```bash
aws logs create-log-group --log-group-name /minishop/app --tags Project=minishop-curso
aws logs put-retention-policy --log-group-name /minishop/app --retention-in-days 7
aws logs describe-log-groups --log-group-name-prefix /minishop --query 'logGroups[0].[logGroupName,retentionInDays]' --output text
```
```text
/minishop/app	7
```
O `deploy/compose.awslogs.yaml` troca o driver de logs dos contêineres (aplicado como segundo arquivo `-f`; validado com `docker compose config`):
```yaml
services:
  web:
    logging:
      driver: awslogs
      options: { awslogs-region: "${AWS_REGION:-sa-east-1}", awslogs-group: /minishop/app, tag: web }
```
É **opt-in**: no primeiro boot os logs vão para o disco (`json-file`, com `max-size`); depois que o papel e o grupo existem, na instância (Session Manager): `touch /opt/minishop/use-awslogs && /opt/minishop/update.sh <tag>`. (Por quê opt-in: se o driver `awslogs` não conseguir criar o fluxo, o **contêiner não inicia**; é melhor descobrir isso com a aplicação já funcionando. **Não executei o driver contra o CloudWatch**: no simulador só validei a configuração.) Para ver os logs: console (*CloudWatch → Log groups → /minishop/app*), `aws logs tail /minishop/app --follow --since 10m`, ou o Logs Insights (exemplo, não executado):
```text
fields @timestamp, @message
| filter @message like /ERROR|Traceback/
| sort @timestamp desc
| limit 50
```

**3. Um alarme (no simulador).**
```bash
aws cloudwatch put-metric-alarm --alarm-name minishop-cpu-alta --namespace AWS/EC2 --metric-name CPUUtilization \
  --dimensions Name=InstanceId,Value=i-0abc --statistic Average --period 300 --evaluation-periods 2 \
  --threshold 80 --comparison-operator GreaterThanThreshold --tags Key=Project,Value=minishop-curso
aws cloudwatch describe-alarms --alarm-names minishop-cpu-alta --query 'MetricAlarms[0].[AlarmName,Threshold,Period]' --output text
```
```text
minishop-cpu-alta	80.0	300
```
"CPU média acima de 80% por 2 períodos de 5 minutos." Na AWS real, acrescente `--alarm-actions` com o ARN de um tópico SNS (e-mail). Alarmes **cobram** e entram na conta: apague-os (`delete-alarms`). Para o faturamento, o orçamento da aula 01 é o instrumento recomendado.

**4. A destruição, e a prova.** Com a infraestrutura criada, simulei **esquecimentos** (em duas execuções: um **IP elástico solto** e um **volume EBS solto**, ambos com a tag). Na execução do volume, antes de destruir, a conferência acusa:
```text
  SOBROU  EC2            i-1bd08b4e710314f99
  SOBROU  EBS            vol-3718b24c4da89437c	vol-046e16d6acd9d0a6f      ← o do disco raiz e o "esquecido"
  SOBROU  Sec. groups    sg-946356404bfd4fad5	sg-974951b79b4af9868
  SOBROU  RDS            minishop-db
  SOBROU  S3             minishop-midia-123456789012
  SOBROU  ECR            minishop
  SOBROU  Logs           /minishop/app
  SOBROU  Parâmetros     /minishop/SECRET_KEY	/minishop/DB_PASSWORD	/mi...
  SOBROU  IAM papel      minishop-ec2
  SOBROU  IAM profile    minishop-ec2
  SOBROU  Tag API        arn:aws:s3:::minishop-midia-123456789012 ...
ATENÇÃO: ainda há recursos.                                              (exit 1)
```
```bash
CONFIRMO=sim bash scripts/aws/destroy.sh
```
```text
== 1/8 EC2                 terminada(s): i-1bd08b4e710314f99
== 2/8 RDS                 banco apagado
== 3/8 Security groups     ok: delete-security-group (banco), depois (web)
== 4/8 Bucket S3           N versão(ões)/objeto(s) removido(s); remove_bucket ok
== 5/8 ECR, logs e parâmetros
== 6/8 IAM                 ok: remove-role-from-instance-profile, delete-instance-profile, delete-role-policy, detach-role-policy, delete-role
== 7/8 IPs elásticos, volumes EBS soltos e snapshots   ok: aws ec2 delete-volume --volume-id vol-046e16d6acd9d0a6f
== 8/8 Conferência         limpo (13 linhas)         TUDO LIMPO (nesta região: sa-east-1). Confira também o painel de Billing amanhã.   (exit 0)
```
Os dois "esquecimentos" foram pegos: o IP elástico e o volume. **Três descobertas que o próprio teste produziu e viraram código:** (1) a primeira versão do script não liberava IPs elásticos: a conferência acusou `SOBROU IP elástico` e acrescentei o passo (um IP elástico **solto é cobrado** só por existir); (2) o `aws s3 rb --force` **não** apaga versões (`BucketNotEmpty`), então criei o `scripts/aws/empty_bucket.py`; (3) a conferência marcava como "sobra" a instância **já terminada**, que a AWS continua listando por cerca de uma hora e **não cobra**: o `verify_clean.sh` agora ignora instâncias `terminated`. E um **erro de shell** meu: uma mensagem do `destroy.sh` continha `` `rb --force` `` entre aspas duplas, e o bash **executou** o comando em vez de imprimi-lo (o sintoma foi o texto sumir da saída). Aprendizado: crases dentro de `"..."` são substituição de comando; em mensagens, use texto simples.

**5. O que continua existindo depois do `destroy.sh` (confira você).**
| Coisa | Cobra? | O que fazer |
|---|---|---|
| Orçamento, monitor de anomalias | não | manter |
| Provedor OIDC e papel de deploy (aula 07) | não | apagar à mão se não for usar (`aws iam delete-open-id-connect-provider`, `delete-role`) |
| Usuários/identidades de estudo | não | revisar |
| Logs já enviados (se o grupo foi mantido) | sim, armazenamento | o `destroy.sh` apaga o grupo |
| Snapshots finais do RDS | sim | o roteiro usa `--skip-final-snapshot`; se você criou um, apague |
| Imagens do ECR | sim | apagadas com `--force` |
| Recursos em **outra região** | sim | `AWS_DEFAULT_REGION=outra bash scripts/aws/verify_clean.sh` |
| Recursos sem a tag | sim | *Resource Explorer*/Tag Editor; painel de custos por serviço |
**No dia seguinte (obrigatório):** *Billing and Cost Management → Cost Explorer (ou Bills)*, agrupe **por serviço** e **por região** e confira que o custo do dia anterior corresponde ao esperado e que **nada novo aparece hoje**. O painel atrasa (horas); por isso o conferir no dia seguinte.

**6. Se o `destroy.sh` falhar no meio.** Leia o erro, que costuma ser uma dependência: `DBSubnetGroupInUse` (o banco ainda existe), `DependencyViolation` ou `InvalidGroup.InUse` (SG em uso), `BucketNotEmpty` (versões), `Cannot delete entity, must detach all policies first` (IAM). Rode de novo (idempotente); se persistir, apague pelo console na mesma ordem. **Nunca** feche a conta achando que isso cancela tudo: a documentação alerta para cobranças após o fechamento. E **não** use `--force`/scripts de limpeza genéricos que apagam "tudo da conta": use a tag.

## 🧠 Pausa para lógica
**Problema.** Seu `verify_clean.sh` imprime `limpo` para EC2, RDS, S3, EBS e IAM. Mesmo assim, no dia seguinte, o painel mostra US$ 0,84 de custo "EC2-Other" e US$ 0,12 de "CloudWatch". (a) Cite **três** causas possíveis, com o campo/serviço envolvido. (b) Quais recursos o script **não enxerga**? (c) Qual a primeira coisa que você olha no painel de custos para achar a causa? (d) Como a tag ajuda e quando ela não ajuda?

<details><summary>Dica</summary>"EC2-Other" agrupa muita coisa que não é a instância. Lembre da região, da tag e do atraso do painel.</details>

<details><summary>Solução comentada</summary>

(a) (1) **IPv4 público/IP elástico** ou **volume EBS** de uma instância terminada ontem (o custo do dia cobre as horas que ela existiu: pode ser só o resíduo do dia, não uma sobra). (2) Recurso criado **em outra região** (a conferência olha uma). (3) **CloudWatch**: logs ingeridos antes da destruição, ou um **alarme/painel** esquecido, ou métricas personalizadas; o grupo apagado já tinha cobrado a ingestão do dia. (b) Outras regiões, recursos sem tag criados à mão, o provedor OIDC/papel de deploy, serviços criados "por baixo" de outros. (c) Agrupar por **serviço**, depois por **tipo de uso** (`UsageType`) e por **região**, e olhar o **dia**: se o custo é só do dia anterior e sumiu hoje, foi resíduo; se continua, há algo vivo. (d) A tag permite filtrar o painel e a API de tags; **não** ajuda quando o recurso foi criado sem tag, ou por um serviço que não propaga a tag.
</details>

## ⚠️ Erros comuns e boas práticas
| Sintoma / mensagem | Causa | Solução |
|---|---|---|
| `ParameterNotFound` ao ler | Caminho/região errados | `--region`; `describe-parameters` |
| `AccessDeniedException … ssm:GetParametersByPath` | Papel sem o `Allow` em `parameter/minishop/*` | Política da aplicação (aula 03) |
| Segredo apareceu em `docker inspect` | Foi parar em `environment:` | `.env` com `600`, `env_file` (e a aula 11.04: o que vaza onde) |
| Logs somem / contêiner não inicia com `awslogs` | Grupo/permissão ausente | Criar o grupo; papel com `logs:CreateLogStream/PutLogEvents`; opt-in |
| Conta de CloudWatch crescendo | Retenção ilimitada | `put-retention-policy` |
| `DependencyViolation` / `InvalidGroup.InUse` ao apagar SG | Ainda em uso | Ordem: instância → banco → SGs |
| `DBSubnetGroupInUse` | Banco ainda existe | `rds wait db-instance-deleted` antes |
| `BucketNotEmpty` | Versões/marcadores | `empty_bucket.py` |
| `SOBROU IP elástico` | EIP solto | `release-address` |
| `verify_clean` "limpo" mas há cobrança | Outra região/sem tag | Painel por serviço e por região |
| O texto de um `echo` sumiu | Crases em aspas duplas viram comando | Evitar crases em mensagens |
| Fechei a conta e continuaram cobrando | O fechamento não apaga recursos nem encerra cobranças pendentes | Destruir **antes**; ler "Understanding unexpected charges" |
- **Tudo de estudo é efêmero:** criar de manhã, destruir à noite, conferir no dia seguinte.
- **Um dono por recurso, uma tag, uma data de validade** (anote no `docs/aws.md`).
- **Não confie só no script:** confira o painel de custos e as regiões.
- **Rotacione segredos que já passaram por chat, e-mail ou print.**
- **Apague o que criou à mão** (provedor OIDC, papéis, usuários de teste).

## 🧩 Exercícios
**1. Fixação.** (a) Parameter Store × Secrets Manager. (b) Por que não colocar segredos no `user-data`? (c) O que é retenção de logs e por que o padrão é perigoso? (d) Por que a ordem de destruição importa? (e) O que o `verify_clean.sh` **não** cobre?

<details><summary>Solução</summary>

(a) Parameter Store: configuração e segredos simples, camada gratuita; Secrets Manager: segredos com rotação, cobrado. (b) O user-data é legível pelos metadados e pelo console e fica em logs de boot. (c) Quanto tempo os eventos ficam guardados; o padrão é ilimitado e cobra armazenamento. (d) Dependências: SG em uso, papel com política anexada, bucket com versões. (e) Outras regiões, recursos sem tag, o que foi criado à mão (OIDC), o orçamento e o faturamento.
</details>

**2. Aplicação no projeto MiniShop (fecha o módulo e o marco `v4.0-aws`).**
- [ ] Os parâmetros do `/minishop/*` (tipos `String` e `SecureString`), o trecho do `.env` executado no simulador, e a prova de que `DB_PASSWORD` não chega ao `.env` e de que o arquivo é `-rw-------`
- [ ] A reescrita da `DATABASE_URL` com `?sslmode=require` (versão 2 do parâmetro)
- [ ] Grupo de logs com **retenção de 7 dias** e o `compose.awslogs.yaml` validado com `docker compose config`; alarme de CPU criado e removido no simulador
- [ ] `destroy.sh` → `verify_clean.sh` executados **com pelo menos dois esquecimentos propositais** (IP elástico e volume), mostrando a conferência acusar e depois ficar `TUDO LIMPO`; e uma execução **repetida** (idempotência)
- [ ] Um teste de versionamento: bucket versionado com 3 versões, `rb --force` falhando e `empty_bucket.py` resolvendo
- [ ] `docs/aws.md` com o **roteiro de destruição** (a ordem dos 8 passos), a lista "o que continua existindo" e o procedimento do dia seguinte (painel por serviço e por região)
- [ ] **Se executou na AWS real:** o print do `verify_clean.sh` (`TUDO LIMPO`) e do painel de custos no dia seguinte. **Se não:** registrar "destruição validada só no simulador"
- [ ] Commit `feat(aws): parameter store config, log retention and destroy runbook`
- [ ] `git tag -a v4.0-aws -m "MiniShop na AWS"` (com a ressalva do [checkpoint](checkpoint.md) sobre o que foi ou não executado na AWS real)

**3. Desafio (opcional).** Troque o Parameter Store por **Secrets Manager** para a senha do RDS, com rotação automática, e ajuste a política IAM e o `user-data`. Estime o custo mensal adicional pela calculadora e decida se vale a pena no MiniShop.

## 🎤 Na entrevista
**1. Onde ficam as senhas e chaves da sua aplicação na nuvem?** Num gerenciador de segredos (Parameter Store `SecureString` ou Secrets Manager), cifrado, com acesso por IAM restrito ao caminho da aplicação; a instância os lê com o papel no boot. Nada no Git, na imagem nem no user-data; credenciais da AWS são temporárias, via papel.

**2. Como você evita custos esquecidos em estudo?** Orçamento e alertas antes de criar; tag em tudo; scripts de criação e de destruição versionados; destruição no mesmo dia com uma conferência por região; e conferência do painel de custos no dia seguinte.

**3. Como você acompanha uma aplicação em produção na AWS?** Logs centralizados no CloudWatch com retenção definida, métricas e alarmes (CPU, erros), health checks, e orçamentos; e depois APM/erros (Sentry) e dashboards, que são o assunto do módulo 14.

## 📚 Para ir além
- 📄 Documentação oficial: [Parameter Store](https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-parameter-store.html) e [Secrets Manager](https://docs.aws.amazon.com/secretsmanager/latest/userguide/intro.html). Tipos, hierarquia, rotação.
- 📄 Documentação oficial: [CloudWatch Logs](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/WhatIsCloudWatchLogs.html) e [driver `awslogs` do Docker](https://docs.docker.com/engine/logging/drivers/awslogs/). Grupos, fluxos, retenção e opções.
- 📄 Documentação oficial: [Understanding unexpected charges](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/checklistforunwantedcharges.html). A lista que o `verify_clean.sh` tenta espelhar.
- 📄 Documentação oficial: [Excluir uma instância RDS](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_DeleteInstance.html) e [excluir um bucket S3](https://docs.aws.amazon.com/AmazonS3/latest/userguide/delete-bucket.html). Snapshot final, backups automáticos, versões.
- 📄 Documentação oficial: [Tags e Tag Editor](https://docs.aws.amazon.com/tag-editor/latest/userguide/tagging.html). Como achar tudo que tem uma tag.
- 📄 Documentação oficial: [AWS Budgets](https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-managing-costs.html) e [Cost Anomaly Detection](https://docs.aws.amazon.com/cost-management/latest/userguide/manage-ad.html).
- 📄 Documentação: [Infraestrutura como código — Terraform](https://developer.hashicorp.com/terraform/intro) e [AWS CDK](https://docs.aws.amazon.com/cdk/v2/guide/home.html). `terraform destroy` faz a destruição a partir de um estado, em vez de uma lista de comandos (só mencionado).
- 🏋️ Prática extra: escreva, para cada recurso do `provision.sh`, **o comando que você usaria para achá-lo manualmente** se o `verify_clean.sh` não existisse, e **uma forma de ele continuar cobrando depois de "apagado"**.

## ✅ Checklist da aula
- [ ] Sei guardar e ler segredos no Parameter Store, sem expô-los (`.env` com `600`)
- [ ] Defini retenção dos logs e sei o que cobra no CloudWatch
- [ ] Sei a ordem de destruição e por quê
- [ ] `destroy.sh` + `verify_clean.sh` rodaram e acusaram os esquecimentos propositais
- [ ] Sei o que o script **não** cobre e vou conferir o painel por serviço e por região no dia seguinte
- [ ] Anotei o que criei à mão e vou apagar
