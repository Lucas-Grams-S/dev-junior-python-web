# 7. Deploy do MiniShop

> ⏱️ ~1h30 · Módulo 13 · Pré-requisitos: [13.04](04-ec2-security-groups-vpc.md), [13.05](05-rds-postgres.md), [13.06](06-s3-midia.md), [12.02 (CD e ambientes)](../12-ci-cd/02-pipeline-completo.md), [11.06 (Nginx e Uvicorn)](../11-docker/06-gunicorn-nginx.md)

> ✅ **Verificação.** Executado: o **pacote de produção** (`deploy/compose.prod.yaml` + `nginx.conf`) num Docker Compose local, com um PostgreSQL de contêiner no lugar do RDS e o `moto` no lugar do S3 (web saudável, migração, estáticos, Nginx, upload de imagem no "bucket"); o `provision.sh` e o `destroy.sh` inteiros contra o `moto`; e a validação do `cd.yml` com o **actionlint**. **Não executado (sem conta AWS):** o deploy numa EC2 real, o `deploy.sh` (push no ECR e Run Command), o `cloud-init`, o job `deploy-aws` do GitHub, a URL pública. **Esta aula não entrega a "URL pública no ar" que o marco `v4.0-aws` pede**: você a obtém executando os scripts na sua conta (💸), e eu documento o que esperar. Código em [`projeto/referencia-api-m13/`](../projeto/referencia-api-m13/README.md).

## 🎯 Objetivos
- Comparar **opções de deploy na AWS** (EC2+Compose, ECS/Fargate, App Runner, Lightsail) e **justificar a escolha pelo custo e pelo aprendizado**
- Descrever o fluxo **imagem → ECR → EC2** e explicar cada etapa do `provision.sh`, do `deploy.sh` e do `update.sh`
- Rodar o **mesmo Compose de produção** localmente para testar antes de gastar
- Configurar o deploy automático pelo GitHub Actions com **OIDC** (sem chaves guardadas)
- Descrever os limites desta arquitetura (um servidor, HTTP sem TLS) e o que mudar para produção de verdade

## 🤔 Por que isso importa
"Funciona na minha máquina" só vira "funciona para os usuários" no deploy. É onde se juntam tudo: imagem, rede, banco, segredos, arquivos e logs. E é onde se decide **quanto custa** e **quanto trabalho dá**. Em entrevista, "como foi o deploy do seu projeto e por que essa escolha?" é pergunta obrigatória, e a resposta madura cita o **custo**, o **risco** e o que faltaria para produção real.

## 💡 Intuição (explicação simples)
Quatro jeitos de abrir uma loja: **alugar o ponto vazio e montar tudo** (EC2: máximo controle, mais trabalho); **alugar um espaço já com balcão e gerente** (ECS/Fargate, App Runner: você traz o produto, eles cuidam do resto, e cobram por isso); **uma banca pronta com preço fixo** (Lightsail). Para **aprender**, montar o ponto vazio ensina o que os outros escondem; para **ganhar tempo**, o gerenciado é melhor.

## 🔬 Como funciona por dentro
**Opções de deploy (comparação conceitual; confira preços e status de cada serviço na documentação do dia)**
| Opção | O que é | Você gerencia | Custo (padrão de cobrança) | Quando escolher |
|---|---|---|---|---|
| **EC2 + Docker Compose** *(a nossa)* | uma VM com Docker | SO, atualizações, Compose, reinício, backups | instância + disco + IPv4 por hora | aprender, projeto pequeno, orçamento baixo |
| **ECS no Fargate** | orquestrador de contêineres sem servidores | definição de tarefas/serviços | por vCPU/memória/hora de tarefa **+ balanceador** | contêineres em produção, escala |
| **App Runner** | publica um contêiner/código com escala e HTTPS prontos | quase nada | por uso/provisionamento | web app simples, equipe pequena (verifique o status atual do serviço) |
| **Lightsail** | VPS com preço mensal fixo e painel simples | SO e aplicação | pacote mensal | sites pequenos, previsibilidade |
| **Elastic Beanstalk** | PaaS que monta EC2/ELB/etc. por você | pouco | os recursos que ele cria | legado/migração |
**Por que EC2 + Compose neste curso:** (1) é a **continuação direta** do módulo 11 (o mesmo Compose roda ali), então o aluno vê o que a plataforma gerenciada esconde; (2) **o menor número de peças cobradas** (um balanceador sozinho já custa por hora; NAT Gateway, idem); (3) conhecimento **portátil** (qualquer VPS Linux). **Contrapartidas honestas:** é **um servidor só** (se cair, o site cai: sem alta disponibilidade); **você** atualiza o SO; a troca de versão tem uma pequena **indisponibilidade** (`recreate`); não há **HTTPS** sem domínio (abaixo). Para produção real com tráfego, ECS/Fargate atrás de um balanceador com certificado do ACM é o caminho; a aplicação (contêiner, `DATABASE_URL`, `STORAGES`) já está pronta para ele.

**Fluxo completo**
```mermaid
flowchart LR
    DEV[git tag v3.2.0] --> GH[GitHub Actions<br/>OIDC, sem chaves]
    GH -->|build + push| ECR[(ECR)]
    GH -->|ssm send-command| EC2
    subgraph EC2["EC2 (Compose)"]
      U[update.sh] -->|pull da tag| ECR
      U --> C[nginx · web · worker · redis]
    end
    C --> RDS[(RDS)]
    C --> S3[(S3)]
    C -. logs .-> CW[CloudWatch Logs]
    P[(Parameter Store)] -. .env no boot .-> EC2
```
- **ECR** (registro de imagens da AWS) em vez do GHCR do módulo 12: a EC2 tem **papel IAM** e baixa do ECR sem token nenhum (com o GHCR privado seria preciso guardar um token). O `cd.yml` ganha o job `deploy-aws`.
- **`update.sh`** (na instância): `ecr get-login-password | docker login` → grava `image.env` com a **tag** → `docker compose pull && up -d --remove-orphans` → `docker image prune`. A tag é o **commit/versão**, nunca `latest` (rollback = rodar o `update.sh` com a tag anterior).
- **`compose.prod.yaml`** (a mesma ideia do módulo 11, com três diferenças): **sem `db`** (o banco é o RDS, `DATABASE_URL` vem do `.env`); o **Redis é um contêiner** na mesma instância, com limite de memória e sem persistência (fila de e-mails, cache: aceitável perder; um ElastiCache seria o serviço gerenciado); e os **estáticos** são copiados da imagem para um volume pelo serviço `static` a cada deploy (o volume nunca fica velho).
- **Segredos:** nada no Git, nada no `user-data`: o boot lê `/minishop/*` do Parameter Store (papel IAM) e grava o `.env` com `umask 077`.

**Limites que você deve saber nomear**
- **Sem TLS.** Sem domínio não há certificado público; a aula usa HTTP para estudar. Cookies `Secure` (sessão do Admin) **não funcionam** em HTTP; a API com JWT funciona. Para HTTPS: domínio + (a) balanceador (ALB) com certificado do **ACM**, ou (b) Let's Encrypt/Caddy na própria instância. **Nunca** coloque credenciais reais num site sem TLS.
- **Um servidor, um ponto de falha;** sem *autoscaling*; atualização com pequena parada.
- **O IP público muda** se a instância for parada e religada (use IP elástico, 💸 se solto, ou DNS).

## 🛠️ Exemplo prático
**1. O Compose de produção, testado localmente antes de gastar.** O arquivo `deploy/compose.prod.yaml` é exatamente o que o `user-data` grava na instância. Para testá-lo, um `override.yaml` só para o teste coloca tudo numa rede onde estão um PostgreSQL de contêiner (o "RDS") e o `moto` (o "S3"), e troca a porta 80 por 8090:
```bash
docker network create lab13net
docker run -d --name lab13-rds  --network lab13net --network-alias rds  -e POSTGRES_USER=minishop -e POSTGRES_PASSWORD=x -e POSTGRES_DB=minishop postgres:18
docker run -d --name lab13-moto --network lab13net --network-alias moto -p 127.0.0.1:5056:5000 motoserver/moto:latest
docker build -t minishop:lab13 .
docker compose -f compose.prod.yaml -f override.yaml --env-file image.env up -d --wait
docker compose -f compose.prod.yaml -f override.yaml --env-file image.env ps --format '{{.Service}}: {{.Status}}'
```
```text
nginx: Up Less than a second
redis: Up 12 seconds (healthy)
web: Up 6 seconds (healthy)
worker: Up 6 seconds
```
(`migrate` e `static` terminaram com sucesso, como tarefas únicas; o `.env` do teste apontava `DATABASE_URL` para `rds` e `AWS_S3_ENDPOINT_URL` para `moto`.) Depois: dados de exemplo, login, **upload de imagem** e verificação no bucket simulado:
```bash
docker compose ... run --rm -e DEBUG=1 web python manage.py seed         # só neste teste local; o seed RECUSA rodar em produção
curl -s -X POST $B/products/49/image/ -H "Authorization: Bearer $TOKEN" -F "image=@foto.png"
curl -s -o /dev/null -w "estático via nginx: %{http_code} server=%header{server}\n" http://127.0.0.1:8090/static/admin/css/base.css
curl -s -o /dev/null -w "docs (EXPOSE_DOCS desligado em prod): %{http_code}\n" http://127.0.0.1:8090/api/docs/
docker compose ... exec -T web id -un
```
```text
Seed ok: 64 produtos
image_url: http://moto:5000/midia-lab/products/cas-049.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=teste%2F20261109%2Fsa-...
2026-11-08 22:48:37        103 cas-049.png
estático via nginx: 200 server=nginx/1.29.8
docs (EXPOSE_DOCS desligado em prod): 404
app
```
O `web` roda como `app` (não root), as docs da API estão desligadas em produção, o estático vem do Nginx, e o upload chegou ao bucket. Um aviso de nomenclatura que vale por si: **o `name:` desse Compose é `minishop-prod`**, e não `minishop`: na minha primeira tentativa o projeto se chamava `minishop` e os volumes `minishop_static`/`minishop_outbox` ficaram a um passo de colidir com o `minishop_pgdata` (aula 11.04). O teste local criou e apagou apenas os seus.

**2. Subir na AWS (💸 gera custo).** Pré-requisitos: aulas 01 (conta, MFA, orçamento) e 03 (identidade). **Confirme `aws sts get-caller-identity`, a região, e `env | grep AWS_` vazio de `AWS_ENDPOINT_URL`.**
```bash
bash scripts/aws/provision.sh           # pede "sim"; cria S3, ECR, logs, parâmetros, IAM, SGs, RDS e EC2 (~10-20 min, por causa do RDS)
bash scripts/aws/deploy.sh              # constrói a imagem (linux/amd64), envia ao ECR e manda a instância atualizar
```
Resultado esperado do `provision.sh` (formato real, valores serão os seus):
```text
Instância: i-0abc...   IP público: 203.0.113.10   (💸 IPv4 público é cobrado por hora)
Bucket:    minishop-midia-<ID da conta>
Banco:     minishop-db.xxxxxxxx.sa-east-1.rds.amazonaws.com
DESTRUIR:  bash scripts/aws/destroy.sh   e conferir:  bash scripts/aws/verify_clean.sh
```
Teste da URL pública (na AWS real; **não executado**):
```bash
IP=203.0.113.10
curl -s -o /dev/null -w "%{http_code}\n" http://$IP/api/v1/products/        # 200
curl -s http://$IP/api/v1/products/ | head -c 200
```
E o **seed** em produção? O comando se recusa (`ALLOW_SEED = DEBUG`). Para ter dados de demonstração em um ambiente de estudo, crie os dados pelo Admin/API ou rode **uma vez** `docker compose exec -e DEBUG=1 web python manage.py seed` pelo Session Manager e **apague os usuários de demonstração depois** (a senha `dev-somente-local-123` é pública no repositório!). Numa produção real isso jamais acontece.

**3. Deploy automático pelo GitHub (OIDC, sem chaves).** O job `deploy-aws` do `cd.yml` (validado pelo **actionlint**, não executado) roda **só em tag `v*`** e só se a variável `AWS_ROLE_ARN` existir:
```yaml
deploy-aws:
  needs: [publish, deploy-staging]
  if: startsWith(github.ref, 'refs/tags/v') && vars.AWS_ROLE_ARN != ''
  environment: production
  permissions: { contents: read, id-token: write }     # pede um token OIDC ao GitHub
  steps:
    - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1  # v7.0.1
    - uses: aws-actions/configure-aws-credentials@e1253824e5c10ff9df46874f81ed3ec929e19cfd  # v6.3.0
      with: { role-to-assume: "${{ vars.AWS_ROLE_ARN }}", aws-region: "${{ vars.AWS_REGION }}" }
    - id: ecr
      uses: aws-actions/amazon-ecr-login@03f1aad4c6c7ffd436567f42f9384779290529bd  # v2.1.7
    - uses: docker/setup-buildx-action@f87e5991a6d7451dcb8d9637bfbc97413f497069  # v4.4.1
    - uses: docker/build-push-action@c3c9e263c25d99ce0380d002d59b67737d91b0dc  # v7.4.0
      with: { context: ".", platforms: linux/amd64, push: true, tags: "${{ steps.ecr.outputs.registry }}/minishop:${{ github.ref_name }}" }
    - run: |   # SSM Run Command → /opt/minishop/update.sh <tag>
```
Como funciona o OIDC: o GitHub emite um token **efêmero** que diz "sou o repositório X, na tag Y"; a AWS (com um *provedor de identidade OIDC* cadastrado e um papel cuja **política de confiança** exige esse repositório e essa tag) troca o token por credenciais temporárias. **Nenhuma chave de acesso fica guardada no GitHub.** Os modelos de política estão em `scripts/aws/policies/` (`github-oidc-trust.json.tpl`: só `repo:<dono>/minishop:ref:refs/tags/v*` assume o papel; `deploy-policy.json.tpl`: só enviar imagem ao ECR e mandar comando às instâncias com a tag do projeto), e ambos passam no `lint_policy.py`. **Ainda é preciso** (manual, no console/CLI, não executado): cadastrar o provedor OIDC `token.actions.githubusercontent.com`, criar o papel de deploy e definir as variáveis `AWS_ROLE_ARN` e `AWS_REGION` no ambiente `production`. Lembre-se da aula 12: **sem proteção de ambiente (plano gratuito privado), esse job roda sem aprovação** assim que a tag existir.

**4. Reversão (rollback).**
```bash
bash scripts/aws/deploy.sh sha-<commit-bom>      # reenvia (ou apenas reaplica) a tag anterior
# ou, direto na instância (Session Manager):  /opt/minishop/update.sh sha-<commit-bom>
```
Como as imagens são imutáveis e identificadas por tag, voltar é reaplicar a tag antiga. O que **não** volta sozinho é o banco: migrações compatíveis com a versão anterior (expandir e contrair, aula 12.02) e backups testados (aula 05).

## 🧠 Pausa para lógica
**Problema.** Você tem 3 opções para hospedar o MiniShop: **A)** EC2 + Compose (custo fixo por hora, 1 servidor); **B)** Fargate com 2 tarefas atrás de um balanceador (custo maior por hora, mas sem parada em deploy); **C)** Lightsail (preço mensal fixo). Sua loja de estudo tem 5 visitas por dia, e você a usará 10 horas por mês. (a) Qual escolher, e por quê? (b) Se o projeto virar uma loja real com 50 mil visitas/dia e a exigência de "no máximo 5 minutos de indisponibilidade por mês", qual muda e por quê? (c) O que **não** muda entre as duas respostas?

<details><summary>Dica</summary>Custo por hora × horas de uso; e o que cada opção entrega em disponibilidade.</details>

<details><summary>Solução comentada</summary>

(a) **A (EC2 + Compose), usada só nas 10 horas e destruída depois**: custo por hora × poucas horas = centavos, e é a que mais ensina. O Lightsail (mensal fixo) paga o mês inteiro por 10 horas; o Fargate + balanceador paga a peça mais cara (o balanceador) por pouca coisa. (b) **B (ou equivalente com alta disponibilidade)**: dois servidores em AZs diferentes, balanceador com verificação de saúde e *rolling update* eliminam a parada nos deploys e toleram queda de uma máquina; a meta de 5 min/mês (≈ 99,99%) é inatingível com um servidor só. (c) A **imagem Docker**, o **PostgreSQL** (RDS, idealmente Multi-AZ), o **S3**, os **segredos** e as **variáveis de ambiente**: a aplicação não muda, só o "hospedeiro". Esse é o ganho de ter seguido os 12 fatores.
</details>

## ⚠️ Erros comuns e boas práticas
| Sintoma / mensagem | Causa | Solução |
|---|---|---|
| Site não abre em `http://IP/` | Boot em andamento, SG sem a porta 80, ou imagem não publicada | `aws ssm start-session`; `tail /var/log/minishop-user-data.log`; rodar `deploy.sh` |
| `400 Bad Request` | `ALLOWED_HOSTS` sem o IP/domínio | O user-data põe o IP público; com domínio, ajuste o parâmetro |
| `pull access denied` / `no basic auth credentials` na EC2 | Falta o `ecr get-login-password` ou o papel sem permissão de ECR | `update.sh` faz o login; revisar a política (`BaixarAImagem`) |
| `exec format error` | Imagem em arquitetura diferente (Graviton × x86) | `docker build --platform linux/amd64` com `t3` |
| `no space left on device` | Imagens antigas e logs sem limite | `docker image prune` (no `update.sh`), `max-size` nos logs, disco maior |
| `connection refused`/`timeout` ao RDS | SG do banco sem origem = SG web, ou `DATABASE_URL` errada | Regra 5432 do SG; endpoint no parâmetro |
| Admin não loga | Cookies `Secure` em HTTP | HTTPS (domínio + certificado) ou usar a API |
| Deploy "funcionou" mas a versão antiga continua | `compose pull` sem mudar a tag, ou cache | Tag nova por deploy; `image.env` |
| `AccessDeniedException` no `send-command` | O papel de deploy sem `ssm:SendCommand` na instância | Política de deploy (condição por tag) |
| Depois de um deploy o site dá 502/504 e só volta reiniciando o Nginx | O Nginx resolve `web` **uma vez** ao iniciar; o contêiner recriado ganhou outro IP | `resolver 127.0.0.11 valid=10s` + `set $django_upstream http://web:8000; proxy_pass $django_upstream;` (medido no módulo 14.01: 502/504 antes, 200 depois) |
| Segredo apareceu nos logs do pipeline | `echo` de variável | Nunca imprimir segredos; OIDC em vez de chaves |
| Esquecer a instância ligada | Estudo sem prazo | Calendário: destruir no mesmo dia (aula 08) |
- **Teste o Compose de produção localmente antes de gastar.** Foi o que pegou o conflito de nomes de volume.
- **Tag imutável por deploy** (commit/versão); `latest` só para atalho de leitura.
- **Healthchecks** e `depends_on: service_healthy` (módulo 11) valem aqui.
- **Sem segredos no user-data nem no Git**; papel IAM para tudo que é AWS.
- **Documente o que você NÃO fez** (HTTPS, alta disponibilidade, WAF, backups cruzados) em `docs/aws.md`.

## 🧩 Exercícios
**1. Fixação.** (a) Por que EC2 + Compose neste curso? Duas contrapartidas. (b) Por que o ECR e não o GHCR na AWS? (c) O que o `update.sh` faz? (d) O que é OIDC e por que é melhor que uma chave? (e) Por que o Redis aqui é um contêiner e não um serviço?

<details><summary>Solução</summary>

(a) Continuidade com o módulo 11, menos peças cobradas e conhecimento portátil; contrapartidas: um ponto de falha e parada no deploy (e SO por sua conta, sem HTTPS sem domínio). (b) A EC2 baixa do ECR com o papel IAM, sem token; do GHCR privado teria de guardar um token. (c) Login no ECR, grava a tag em `image.env`, `compose pull` e `up -d`, limpa imagens. (d) O GitHub emite um token efêmero que a AWS troca por credenciais temporárias, condicionado ao repositório e à tag; não há chave guardada. (e) Para estudo (menos custo); perder fila/cache é aceitável; ElastiCache seria o gerenciado.
</details>

**2. Aplicação no projeto MiniShop (fecha o marco `v4.0-aws`, com a ressalva abaixo).**
- [ ] `deploy/compose.prod.yaml`, `nginx.conf`, `user-data.sh.tpl` revisados; `name:` do Compose **único**; `docker compose config` válido
- [ ] **Teste local do pacote de produção** (banco e S3 simulados) com a saída do `ps`, do upload no bucket, do estático e de `id -un`
- [ ] `actionlint` limpo no `cd.yml` com o job `deploy-aws`; as políticas OIDC/deploy passando no `lint_policy.py`
- [ ] **Na sua conta (💸), se decidir executar:** `provision.sh` + `deploy.sh`, a URL pública respondendo `200` em `/api/v1/products/`, o print, e o **`destroy.sh` + `verify_clean.sh` no mesmo dia** (aula 08). Se **não** executar, registre em `docs/aws.md`: "marco `v4.0-aws` cumprido parcialmente: scripts e pacote validados em simulador/local, sem URL pública"
- [ ] `docs/aws.md`: diagrama, a decisão EC2 × alternativas (custo, risco, o que falta para produção) e o procedimento de rollback
- [ ] Commit `feat(aws): production compose, deploy scripts and oidc job`

**3. Desafio (opcional).** Escreva o equivalente da pilha em **ECS/Fargate** (definição de tarefa, serviço, balanceador) **sem criar nada**, e uma tabela comparando o número de recursos e o custo estimado (pela calculadora) das duas arquiteturas. Quando valeria migrar?

## 🎤 Na entrevista
**1. Como foi o deploy do seu projeto e por que essa escolha?** Imagem Docker publicada no ECR e executada num Docker Compose numa EC2, com PostgreSQL no RDS, mídia no S3 e segredos no Parameter Store; escolhi pelo custo e pelo aprendizado, ciente de que é um único servidor, sem HTTPS por não ter domínio; em produção real usaria Fargate/ECS atrás de um balanceador com certificado gerenciado.

**2. Como o pipeline faz deploy sem guardar chaves da AWS?** O GitHub Actions usa OIDC: pede um token efêmero ao GitHub, a AWS o troca por credenciais temporárias de um papel cuja confiança restringe repositório e tag, e o papel de deploy só pode enviar imagens ao ECR e disparar o comando de atualização.

**3. Como você faria rollback?** Reimplantando a tag anterior da imagem (imutável), com migrações compatíveis e backup do banco para o caso de mudanças destrutivas.

## 📚 Para ir além
- 📄 Documentação oficial: [Amazon ECR](https://docs.aws.amazon.com/AmazonECR/latest/userguide/what-is-ecr.html). Repositórios, autenticação e varredura.
- 📄 Documentação oficial: [GitHub Actions + OIDC na AWS](https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-aws). Provedor, papel e condições `sub`.
- 📄 Documentação oficial: [User data](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/user-data.html) e [Session Manager](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager.html).
- 📄 Documentação: [Docker Compose em produção](https://docs.docker.com/compose/how-tos/production/) (em inglês). O que muda do desenvolvimento.
- 📄 Documentação: [Django — Checklist de deploy](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/) e [Well-Architected](https://aws.amazon.com/architecture/well-architected/). Os pilares para a próxima evolução.
- 📄 Ferramenta: [Calculadora de preços da AWS](https://calculator.aws/). Compare A, B e C do exercício.
- 🏋️ Prática extra: leia o `compose.prod.yaml` e, para cada serviço, escreva em uma frase **o que acontece com o site se ele cair** e se o `restart: unless-stopped` resolve.

## ✅ Checklist da aula
- [ ] Sei comparar EC2+Compose, Fargate, App Runner e Lightsail por custo e trabalho
- [ ] Sei o fluxo imagem → ECR → EC2 e o papel de `provision.sh`, `deploy.sh` e `update.sh`
- [ ] Testei o Compose de produção localmente antes de gastar
- [ ] Sei como o OIDC dispensa chaves guardadas no GitHub
- [ ] Sei nomear os limites (um servidor, HTTP sem TLS) e o caminho para produção real
- [ ] Defini quando e como vou destruir tudo
