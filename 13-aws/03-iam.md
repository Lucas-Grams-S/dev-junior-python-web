# 3. IAM: usuários, papéis e políticas

> ⏱️ ~1h30 · Módulo 13 · Pré-requisitos: [13.01](01-conceitos-conta-mfa-custos.md), [9.05 (controle de acesso)](../09-seguranca/05-controle-acesso-idor.md), [9.06 (segredos)](../09-seguranca/06-segredos-dependencias-headers-rate-limit.md)

> ✅ **Verificação.** Executado: o **lint de políticas** (`scripts/aws/lint_policy.py`), a criação de papel, política e *instance profile* pelo `provision.sh` **contra o `moto`** (que aceita os comandos mas **não avalia permissões**), e a cadeia de credenciais do `boto3`. **Não executado (sem conta AWS):** a avaliação real de permissões, o IAM Access Analyzer, o IAM Identity Center e qualquer `AccessDenied`. As mensagens de erro da AWS que aparecem abaixo vêm da documentação, não de uma execução minha. Código em [`projeto/referencia-api-m13/`](../projeto/referencia-api-m13/README.md).

## 🎯 Objetivos
- Diferenciar **usuário, grupo, papel e política** e dizer quando usar cada um
- Ler e escrever uma **política JSON** (Effect, Action, Resource, Condition) com **menor privilégio**
- Explicar a **ordem de avaliação** (negação explícita > permissão > negação implícita)
- Dar **permissões a uma aplicação sem chave de acesso**, usando um papel de instância
- Explicar a **cadeia de credenciais** do SDK e por que o código não carrega segredos da AWS

## 🤔 Por que isso importa
IAM (*Identity and Access Management*) decide **quem pode fazer o quê, em qual recurso**. Quase todo incidente de segurança em nuvem passa por IAM: chave vazada, política com `"*"` em tudo, bucket público. Para o júnior, é a habilidade que separa "subi uma EC2" de "subi uma EC2 que não pode destruir a conta se for invadida". E é o assunto mais perguntado em entrevista de nuvem.

## 💡 Intuição (explicação simples)
Um prédio comercial. O **crachá** (identidade) diz quem você é; o **perfil de acesso** (política) diz em quais portas o crachá abre. O **usuário** é um crachá permanente de pessoa; o **papel** é um **crachá de visitante temporário**, que alguém (uma pessoa, um serviço, uma máquina) "veste" por algumas horas e depois devolve. Para um funcionário, você dá acesso só às salas do trabalho dele (menor privilégio), não a chave-mestra. Para o **servidor** da aplicação, em vez de lhe entregar um crachá permanente (que pode ser roubado e copiado), o prédio reconhece a própria máquina e lhe empresta um crachá temporário que se renova sozinho.

## 🔬 Como funciona por dentro
**Os elementos**
| Elemento | O que é | Credencial | Uso típico |
|---|---|---|---|
| **Usuário raiz** | dono da conta | e-mail + senha (+ MFA) | quase nunca |
| **Usuário IAM** | pessoa ou programa, permanente | senha/chave de acesso (de longa duração) | evite; prefira o Identity Center |
| **Grupo** | conjunto de usuários com as mesmas permissões | (nenhuma) | "desenvolvedores" |
| **Papel (role)** | identidade **assumível**, sem credencial própria | **temporária**, via STS | aplicações, serviços, acesso entre contas, pessoas via SSO |
| **Política (policy)** | documento JSON de permissões | (nenhuma) | anexada a usuário, grupo ou papel |
| **Instance profile** | "embrulho" que liga um papel a uma EC2 | temporária, renovada sozinha | a aplicação na EC2 |
| **IAM Identity Center** | login único para pessoas | temporária | acesso de pessoas à conta |

**A anatomia de uma política**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "MidiaDoMiniShop",
      "Effect": "Allow",
      "Action": ["s3:PutObject", "s3:GetObject", "s3:DeleteObject"],
      "Resource": "arn:aws:s3:::minishop-midia-123456789012/products/*"
    }
  ]
}
```
- **Effect:** `Allow` ou `Deny`. **Action:** o que (`serviço:operação`). **Resource:** em quê, pelo **ARN** (identificador único de recurso). **Condition:** quando (por IP, tag, horário, MFA presente…). **Principal:** *quem*, usado nas políticas **de recurso** (ex.: de bucket) e na de **confiança** do papel.
- **Política de identidade** (anexada a quem pede) × **de recurso** (anexada ao recurso, como a política de um bucket) × **de confiança** (diz *quem pode assumir* o papel).

**Ordem de avaliação.** (1) Tudo começa **negado** (negação implícita). (2) Um `Allow` aplicável libera. (3) Um `Deny` explícito aplicável **sempre vence**, mesmo com `Allow`. Há ainda outras camadas (limites de permissão, políticas de controle de serviço da organização), que não usaremos. Logo: **só se faz o que alguma política permite explicitamente, e nada que alguma negue explicitamente.**

**Papel de instância (o jeito certo de dar acesso à aplicação).**
```mermaid
sequenceDiagram
    participant A as Aplicação (boto3)
    participant M as Metadados da EC2 (169.254.169.254)
    participant S as AWS STS
    participant S3 as S3
    A->>M: pede credenciais do papel (IMDSv2)
    M->>S: obtém credenciais TEMPORÁRIAS
    M-->>A: AccessKey + SecretKey + Token (expiram em horas)
    A->>S3: PutObject (assinado com a credencial temporária)
    Note over A,M: o SDK renova antes de expirar; NADA fica no código nem no Git
```
**Cadeia de credenciais do SDK (boto3).** O SDK procura credenciais **nesta ordem** (resumo): parâmetros explícitos no código → **variáveis de ambiente** (`AWS_ACCESS_KEY_ID`...) → arquivos `~/.aws/credentials` e `~/.aws/config` (perfis, SSO) → **credenciais do container** → **metadados da instância EC2**. Por isso o código do MiniShop **não menciona credenciais**: no seu computador o SDK acha o seu perfil; na EC2, acha o papel; nos testes, as variáveis falsas.

**Princípios**
- **Menor privilégio:** conceda só as ações (`PutObject`, não `s3:*`), nos recursos exatos (o prefixo `products/*`, não o bucket inteiro), e só para quem precisa. Comece restrito e abra conforme o erro `AccessDenied` pedir, em vez de começar aberto e "fechar depois".
- **Sem chaves permanentes** quando houver alternativa (papel, SSO). Se uma chave existir: rotacionar, nunca no Git, MFA para operações sensíveis.
- **Uma identidade por finalidade** (um papel para a aplicação, outro para o deploy, outro para você), para saber quem fez o quê e limitar estragos.

## 🛠️ Exemplo prático
**1. O papel da aplicação do MiniShop** (`scripts/aws/policies/`). A **política de confiança** diz que *a EC2* pode assumir o papel:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    { "Effect": "Allow", "Principal": { "Service": "ec2.amazonaws.com" }, "Action": "sts:AssumeRole" }
  ]
}
```
E a **política de permissões** (`app-policy.json.tpl`, com `__BUCKET__` trocado pelo nome real) concede apenas o que a aplicação usa: mídia no prefixo `products/`, leitura dos parâmetros `/minishop/*`, escrita nos logs `/minishop/*`, e baixar a imagem do ECR:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    { "Sid": "MidiaDoMiniShop", "Effect": "Allow", "Action": ["s3:PutObject", "s3:GetObject", "s3:DeleteObject"],
      "Resource": "arn:aws:s3:::__BUCKET__/products/*" },
    { "Sid": "ListarSoOPrefixoProducts", "Effect": "Allow", "Action": "s3:ListBucket",
      "Resource": "arn:aws:s3:::__BUCKET__", "Condition": { "StringLike": { "s3:prefix": "products/*" } } },
    { "Sid": "LerSegredosDoMiniShop", "Effect": "Allow", "Action": ["ssm:GetParameter", "ssm:GetParameters", "ssm:GetParametersByPath"],
      "Resource": "arn:aws:ssm:*:*:parameter/minishop/*" },
    { "Sid": "EscreverLogs", "Effect": "Allow", "Action": ["logs:CreateLogStream", "logs:PutLogEvents"],
      "Resource": "arn:aws:logs:*:*:log-group:/minishop/*:*" },
    { "Sid": "BaixarAImagem", "Effect": "Allow", "Action": ["ecr:GetDownloadUrlForLayer", "ecr:BatchGetImage", "ecr:BatchCheckLayerAvailability"],
      "Resource": "arn:aws:ecr:*:*:repository/minishop" },
    { "Sid": "LoginNoECR", "Effect": "Allow", "Action": "ecr:GetAuthorizationToken", "Resource": "*" }
  ]
}
```
Repare no que **não** está: nada de `s3:*`, `ssm:PutParameter` (a aplicação não escreve segredos), `ec2:*`, `iam:*`. Se um invasor tomar a instância, ele alcança **só** a mídia dos produtos, os parâmetros do MiniShop e o log; não consegue criar máquinas, apagar o banco nem ler outros buckets. O único `"*"` em `Resource` é o de `ecr:GetAuthorizationToken`, que **não aceita recurso específico** (está na documentação; o lint tem essa exceção por escrito).

**2. Um lint para o erro mais comum.** Antes de aplicar qualquer política, `scripts/aws/lint_policy.py` procura `Action` ampla, `Resource: "*"` sem justificativa e `NotAction`/`NotResource`:
```bash
python3 scripts/aws/lint_policy.py scripts/aws/policies/ec2-trust.json scripts/aws/policies/app-policy.json.tpl
python3 scripts/aws/lint_policy.py politica-ruim.json
```
```text
OK  scripts/aws/policies/ec2-trust.json
OK  scripts/aws/policies/app-policy.json.tpl
ERRO politica-ruim.json
   - Tudo: ação ampla demais (s3:*)
   - Tudo: Resource '*' sem justificativa para ['s3:*']
   - Admin: ação ampla demais (*)
   - Admin: Resource '*' sem justificativa para ['*']
```
É uma rede de segurança **simples** (e o `provision.sh` a roda antes de aplicar). Ela **não** entende condições nem a semântica real; quem valida de verdade é o **IAM Access Analyzer** (validação de políticas e achados de acesso externo), que exige conta e **não executei**.

**3. Criar o papel e o instance profile (CLI).** É o passo 4 do `provision.sh`; executei contra o `moto`:
```bash
aws iam create-role --role-name minishop-ec2 --assume-role-policy-document file://scripts/aws/policies/ec2-trust.json --tags Key=Project,Value=minishop-curso
aws iam put-role-policy --role-name minishop-ec2 --policy-name app --policy-document file:///tmp/minishop-app-policy.json
aws iam attach-role-policy --role-name minishop-ec2 --policy-arn arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore
aws iam create-instance-profile --instance-profile-name minishop-ec2
aws iam add-role-to-instance-profile --instance-profile-name minishop-ec2 --role-name minishop-ec2
```
A política gerenciada `AmazonSSMManagedInstanceCore` (mantida pela AWS) permite que o **Systems Manager** acesse a instância: é o que nos permite **entrar e atualizar sem abrir a porta 22** (aula 04). Duas coisas aprendidas na execução: (1) o `moto` **não** conhecia essa política gerenciada até eu iniciá-lo com `MOTO_IAM_LOAD_MANAGED_POLICIES=true` (`NoSuchEntity: Policy … does not exist or is not attachable`); na AWS real ela existe. (2) a ordem de destruição precisa remover o papel do *instance profile*, apagar o profile, **desanexar** e apagar as políticas, e só então apagar o papel (o `destroy.sh` faz isso).

**4. A cadeia de credenciais, na prática.**
```python
import os, boto3
# (sem arquivos de configuração, sem acesso aos metadados, só para o teste)
print("sem nada configurado ->", boto3.Session().get_credentials())
os.environ["AWS_ACCESS_KEY_ID"] = "AKIAEXEMPLO"; os.environ["AWS_SECRET_ACCESS_KEY"] = "x"
print("com variáveis de ambiente ->", boto3.Session().get_credentials().method)
```
```text
sem nada configurado -> None
com variáveis de ambiente -> env
```
O mesmo código achará `sso`, `shared-credentials-file` ou `iam-role` conforme o lugar onde roda. Nos testes do MiniShop (aula 06) as credenciais são **falsas** (variáveis de ambiente), e o `moto` não as valida.

**5. O que o `AccessDenied` diz (documentação, não executado).** Quando falta permissão, a AWS responde algo como `User: arn:aws:sts::123456789012:assumed-role/minishop-ec2/i-0abc is not authorized to perform: s3:PutObject on resource: "arn:aws:s3:::meu-bucket/uploads/x.png" because no identity-based policy allows the s3:PutObject action`. Leia as três partes: **quem** (o papel), **o quê** (a ação) e **em quê** (o ARN). O caminho `uploads/x.png` **não** bate com `products/*`: é assim que o menor privilégio aparece na prática, e a correção é corrigir o código (o prefixo), não ampliar a política para `*`.

## 🧠 Pausa para lógica
**Problema.** Um papel tem duas políticas: **(A)** `Allow s3:* em arn:aws:s3:::dados/*`; **(B)** `Deny s3:DeleteObject em arn:aws:s3:::dados/financeiro/*`. Diga, para cada requisição, se é permitida: (1) `GetObject dados/logo.png`; (2) `DeleteObject dados/logo.png`; (3) `DeleteObject dados/financeiro/2026.csv`; (4) `PutObject outro-bucket/x`; (5) `GetObject dados/financeiro/2026.csv`.

<details><summary>Dica</summary>Comece negando tudo. Um Allow libera; um Deny aplicável vence qualquer Allow.</details>

<details><summary>Solução comentada</summary>

(1) **Permitida**: A cobre, B não se aplica. (2) **Permitida**: A cobre `s3:*`; B só nega o prefixo `financeiro/`. (3) **Negada**: o Deny explícito de B vence o Allow de A. (4) **Negada**: nenhum Allow cobre `outro-bucket` (negação implícita). (5) **Permitida**: B nega só `DeleteObject`; ler continua liberado por A. Moral: o `Deny` é um *cinto de segurança* para exceções; a base é o `Allow` mínimo. E A (`s3:*`) já é ampla demais: o lint a reprovaria.
</details>

## ⚠️ Erros comuns e boas práticas
| Sintoma / mensagem | Causa | Solução |
|---|---|---|
| `AccessDenied … no identity-based policy allows the X action` | Falta o `Allow` para a ação/recurso | Ler quem/ação/ARN; acrescentar **só** o necessário |
| `Policy … does not exist or is not attachable` (no `moto`) | Política gerenciada não carregada no simulador | `MOTO_IAM_LOAD_MANAGED_POLICIES=true` |
| `An error occurred (EntityAlreadyExists)` ao rodar de novo | Recurso já criado | Idempotência: `destroy.sh` ou checar antes |
| `Cannot delete entity, must detach all policies first` | Ordem de remoção | Desanexar/apagar políticas e tirar do *instance profile* antes do papel |
| `Unable to locate credentials` | Cadeia vazia | Perfil/SSO, variáveis, ou papel da instância |
| Política "funciona" só com `*` | Prefixo/ARN errado | Corrigir o recurso; não ampliar |
| Chave de acesso no código/Git | Atalho | Papel (na EC2), SSO (na máquina), segredo em Parameter Store |
| `iam:PassRole` negado ao lançar a EC2 | Quem cria a instância precisa poder "passar" o papel | Permissão `iam:PassRole` restrita àquele papel |
| `Resource: "arn:aws:s3:::bucket"` para `PutObject` | Objetos exigem `bucket/*` | `bucket` para `ListBucket`, `bucket/*` para objetos |
- **Comece negando tudo**; abra pelo `AccessDenied`.
- **Condições** (`aws:MultiFactorAuthPresent`, `aws:SourceIp`, tags) endurecem ações sensíveis.
- **Revise acessos** periodicamente (o IAM mostra o "último uso" de chaves e permissões).
- **Papéis para máquinas, SSO para pessoas, chave permanente para ninguém.**

## 🧩 Exercícios
**1. Fixação.** (a) Usuário × papel. (b) O que faz a política de confiança? (c) Em que ordem o IAM decide? (d) Por que `s3:PutObject` pede `bucket/*` e `s3:ListBucket` pede `bucket`? (e) Para que o *instance profile*?

<details><summary>Solução</summary>

(a) Usuário é permanente, com credencial própria; papel é assumido e dá credencial temporária. (b) Diz quem pode assumir o papel. (c) Negação implícita; `Allow` libera; `Deny` explícito vence. (d) Objetos são recursos dentro do bucket (`/*`); listar é uma operação sobre o próprio bucket. (e) Liga o papel à EC2 para que ela receba credenciais temporárias.
</details>

**2. Aplicação no projeto MiniShop.**
- [ ] `scripts/aws/policies/ec2-trust.json` e `app-policy.json.tpl` revisados por você, e `lint_policy.py` retornando `OK`
- [ ] Um `politica-ruim.json` com **3 defeitos** (por exemplo `s3:*`, `Resource: "*"`, `NotAction`) e o lint reprovando
- [ ] Uma **terceira política** para um papel de **deploy** (pode enviar imagem ao ECR e acionar o Systems Manager, nada além) e o lint aprovando
- [ ] `docs/iam.md`: tabela *quem* (você, a EC2, o pipeline) × *papel* × *o que pode* × *como se autentica* (SSO / instance profile / OIDC), sem nenhuma chave permanente
- [ ] Demonstração do `boto3` mostrando de onde vem a credencial em **dois** cenários (variáveis e perfil)
- [ ] Rodar a parte IAM do `provision.sh` no `moto` e o `destroy.sh` e mostrar que o papel sumiu (`aws iam list-roles`)
- [ ] Commit `feat(aws): least-privilege iam role and policy lint`

**3. Desafio (opcional).** Escreva uma política que permite à aplicação ler objetos do bucket **somente quando a requisição vem pelo endpoint VPC do S3** (condição `aws:SourceVpce`), e explique em que ela difere da que usamos. (Não será possível testá-la sem conta.)

## 🎤 Na entrevista
**1. Qual a diferença entre usuário IAM e papel?** O usuário tem credenciais permanentes e representa uma pessoa ou programa; o papel é uma identidade assumível, sem credencial própria, que fornece credenciais temporárias. Para aplicações em EC2 usa-se papel, nunca chave de acesso embutida.

**2. O que é o princípio do menor privilégio e como você o aplica?** Conceder só as ações necessárias nos recursos exatos, para quem precisa. Na prática: política por finalidade, ARNs específicos, condições quando cabem, começar restrito e ampliar guiado pelo `AccessDenied`, e revisar o uso.

**3. Como sua aplicação na EC2 acessa o S3 sem chaves?** Pelo papel associado à instância (instance profile): o SDK pega credenciais temporárias dos metadados da instância (IMDSv2) e as renova sozinho; a política do papel limita ao bucket/prefixo da aplicação.

## 📚 Para ir além
- 📄 Documentação oficial: [Boas práticas de segurança no IAM](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html). Menor privilégio, credenciais temporárias, MFA, revisão.
- 📄 Documentação oficial: [Políticas e permissões](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies.html) e [Papéis](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles.html). Tipos de política e lógica de avaliação.
- 📄 Documentação oficial: [Papéis do IAM para EC2](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/iam-roles-for-amazon-ec2.html). Instance profile e credenciais temporárias.
- 📄 Documentação oficial: [Validação de políticas (IAM Access Analyzer)](https://docs.aws.amazon.com/IAM/latest/UserGuide/access-analyzer-policy-validation.html). A ferramenta que o lint do curso **não** substitui.
- 📄 Documentação: [`boto3` — credenciais](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html). A cadeia de busca completa.
- 📄 Documentação oficial: [GitHub Actions com OIDC na AWS](https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-aws). Como o pipeline do módulo 12 assume um papel sem guardar chaves (não executado).
- 🏋️ Prática extra: monte, só em papel, as políticas de três pessoas (desenvolvedora, estagiário de leitura, o pipeline) e para cada uma escreva a **pior coisa** que ela poderia fazer se a credencial vazasse.

## ✅ Checklist da aula
- [ ] Sei usuário, grupo, papel, política e instance profile
- [ ] Sei ler uma política e a ordem de avaliação
- [ ] A política da aplicação é de menor privilégio e passa no lint
- [ ] Entendo a cadeia de credenciais e por que não há chaves no código
- [ ] Sei interpretar um `AccessDenied` em quem/ação/recurso
