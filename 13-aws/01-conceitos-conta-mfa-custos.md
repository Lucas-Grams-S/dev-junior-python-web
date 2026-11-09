# 1. Conceitos de nuvem, conta, MFA e alerta de custos

> ⏱️ ~1h30 · Módulo 13 · Pré-requisitos: [Módulo 12 (checkpoint aprovado)](../12-ci-cd/checkpoint.md), [11.04 (segredos e variáveis)](../11-docker/04-volumes-redes-env.md)

> ✅ **Verificação (leia, vale para o módulo todo).** **Não havia conta AWS no laboratório.** O que foi executado: a AWS CLI v2 (2.39.5) e os **scripts do módulo contra o `moto`**, um *simulador* de AWS em Python, e o pacote de deploy num Docker Compose local (PostgreSQL de container no lugar do RDS, `moto` no lugar do S3). Isso valida sintaxe, ordem, idempotência e lógica, **mas não** preços, tempos, limites do plano e permissões reais. Cada afirmação sobre custos e planos vem da documentação oficial (lida em 2026-11-08/09) e você deve **reconferi-la antes de criar a conta**: preços e regras mudam. 💸 marca tudo o que pode gerar cobrança. Código em [`projeto/referencia-api-m13/`](../projeto/referencia-api-m13/README.md).

## 🎯 Objetivos
- Diferenciar **IaaS, PaaS e SaaS** e situar EC2, RDS, S3 e o resto nessa escada
- Explicar **região, zona de disponibilidade** e o **modelo de responsabilidade compartilhada**
- Criar uma conta **do jeito seguro**: MFA no usuário raiz, sem usar a raiz no dia a dia
- Configurar **orçamento e alertas de custo antes de criar qualquer recurso**
- Reconhecer as **armadilhas de cobrança** mais comuns e saber onde olhar

## 🤔 Por que isso importa
"Fui estudar AWS e recebi uma fatura de R$ 1.800" é uma história que se repete: um banco esquecido ligado, um IP elástico solto, uma chave vazada no GitHub usada para minerar criptomoedas. Em entrevista, quem diz "sei AWS" mas não sabe configurar MFA, alerta de custo e menor privilégio levanta bandeira vermelha. Esta aula vem **antes de qualquer recurso** porque tudo que gera cobrança depende dela.

## 💡 Intuição (explicação simples)
Antes, para ter um servidor você comprava e instalava uma máquina. A nuvem é o **aluguel por hora**: você pede uma máquina (ou um banco, ou um armário de arquivos), usa e devolve, pagando só pelo tempo e pelo uso. É como a diferença entre comprar um carro e usar aplicativos de transporte. A conta é como um **cartão de crédito sem limite**: nada impede você de pedir mais, e a fatura chega depois. Por isso, antes da primeira corrida, você cadastra **alarme de gasto** e **senha dupla** no cartão.

## 🔬 Como funciona por dentro
**IaaS × PaaS × SaaS** (quanto você gerencia):
| Modelo | Você gerencia | O provedor gerencia | Exemplo |
|---|---|---|---|
| **IaaS** (infraestrutura) | sistema operacional, runtime, aplicação, dados | hardware, rede, virtualização | **EC2** (uma máquina virtual) |
| **PaaS** (plataforma) | aplicação e dados | o resto, inclusive o sistema operacional | **RDS** (banco gerenciado), App Runner, Elastic Beanstalk |
| **SaaS** (software) | só o uso | tudo | Gmail, GitHub, Sentry |
O curso usa EC2 (IaaS) para a aplicação, RDS (PaaS) para o banco e S3 (armazenamento como serviço) para os arquivos. **Quanto mais gerenciado, menos trabalho operacional e mais custo, e menos controle.**

**Regiões e zonas de disponibilidade.** Uma **região** é uma área geográfica com vários data centers (`sa-east-1` = São Paulo, `us-east-1` = Norte da Virgínia). Dentro dela há **zonas de disponibilidade (AZ)**: data centers isolados entre si, ligados por rede rápida (`sa-east-1a`, `1b`, `1c`). Escolha a região pela **latência** (perto dos usuários), pelos **preços** (variam por região) e por **requisitos legais** (LGPD e localização de dados). Quase tudo é **por região**: um recurso criado em São Paulo não aparece quando você olha `us-east-1`, e **é por isso que se paga por coisas que não se enxergam** (armadilha abaixo).

**Responsabilidade compartilhada.** A AWS é responsável pela segurança **DA** nuvem (prédios, hardware, hipervisor). Você é responsável pela segurança **NA** nuvem: quem tem acesso (IAM), os dados, a configuração (um bucket S3 público é erro **seu**), o sistema operacional da EC2, as atualizações, as portas abertas. Em serviços gerenciados como o RDS, a AWS cuida do sistema operacional e do banco instalado, e você, das senhas, das redes e dos dados.

**Conta, plano e créditos.** Ao criar a conta você escolhe um **plano**. Pela documentação da AWS (lida em 2026-11-09): novos clientes recebem créditos (US$ 100 ao criar a conta, e até US$ 100 adicionais ao concluir atividades); o **plano gratuito (*Free*)** dura **até seis meses ou até os créditos acabarem**, sem cobrança até você migrar para o plano pago, mas **não dá acesso a todos os serviços** (alguns que consumiriam o crédito rapidamente ficam de fora); o **plano pago** cobra o uso comum quando o crédito acaba. Há também ofertas "sempre gratuitas" com limites mensais. A página de planos listava EC2, S3 e RDS como disponíveis nos dois planos. **Regras como estas mudaram ao longo dos anos** (o antigo "12 meses grátis com `t2.micro`" não é o modelo atual): leia [a página do Free Tier](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/free-tier.html) no dia em que criar a conta, e confira quais tipos de instância o seu plano aceita.

**Usuário raiz e MFA.** O e-mail com que você criou a conta é o **usuário raiz**: pode tudo, inclusive fechar a conta e alterar o faturamento, e **não pode ser restringido** por políticas comuns. Regras de ouro (documentação de boas práticas do IAM): (1) ative **MFA** (um aplicativo autenticador, uma chave física ou *passkey*) no usuário raiz **antes de qualquer coisa**; (2) **não crie chaves de acesso** para o usuário raiz; (3) use a raiz **só** para as poucas tarefas que a exigem; (4) crie outra identidade para o dia a dia, com permissões limitadas (aula 03).

**Custos: três camadas de defesa.**
1. **Orçamento (AWS Budgets):** você define um valor mensal e recebe e-mail quando o gasto *real* passa de X% ou quando a *previsão* passa de 100%. É um **alerta, não um freio**: a AWS não derruba seus recursos ao atingir o orçamento (existem ações automáticas de orçamento, mas exigem configuração).
2. **Detecção de anomalias (Cost Anomaly Detection):** avisa quando o padrão de gasto foge do normal.
3. **Disciplina:** tag em tudo, destruição no mesmo dia e conferência no painel de faturamento no dia seguinte.
O painel de faturamento tem **atraso** (horas); um alerta chega *depois* do gasto. Nada substitui apagar as coisas.

## 🛠️ Exemplo prático
> 💸 **Nada desta aula cria recurso pago.** Criar a conta, o MFA e o orçamento é gratuito (confirme na sua conta). Se você não for criar conta agora, faça os passos 3 e 4, que rodam sem conta.

**1. Criar a conta e proteger a raiz (no navegador).** (1) Cadastro em `aws.amazon.com` (exige um cartão, ainda que no plano gratuito). (2) Escolha o **plano gratuito** se o seu plano for novo. (3) *Console → nome da conta → Credenciais de segurança → Autenticação multifator → Atribuir MFA*, com um aplicativo autenticador. (4) **Guarde os códigos de recuperação fora do seu computador** (gerenciador de senhas). (5) Confirme que a raiz **não** tem chave de acesso (a mesma tela).

**2. Criar uma identidade para o dia a dia.** O caminho recomendado hoje é o **IAM Identity Center** (login único, credenciais temporárias); um usuário IAM com MFA também serve para estudo. Detalhes na aula 03. Em ambos, **o MFA é obrigatório** também para essa identidade.

**3. Instalar e testar a CLI (sem conta).**
```bash
aws --version
aws sts get-caller-identity       # sem credenciais, ela diz que não achou: normal
```
```text
aws-cli/2.39.5 Python/3.14.8 Linux/7.0.0-42-generic exe/x86_64.ubuntu.26
Unable to locate credentials. You can configure credentials by running "aws login".
```
Com a conta criada, configure as credenciais **temporárias** (`aws configure sso`, ou `aws login`) em vez de chaves de acesso permanentes, e confirme **qual conta e qual identidade** você está usando antes de cada comando que cria algo:
```bash
aws sts get-caller-identity --query '[Account,Arn]' --output text
aws configure get region
```

**4. Praticar sem risco: o simulador `moto`.** O `moto` implementa a API de dezenas de serviços na sua máquina. A CLI aceita um endereço alternativo pela variável `AWS_ENDPOINT_URL`, e assim **o mesmo comando** roda no simulador ou na AWS:
```bash
uv run moto_server -p 5055 &                        # (no projeto do módulo 13)
export AWS_ENDPOINT_URL=http://127.0.0.1:5055 AWS_ACCESS_KEY_ID=teste AWS_SECRET_ACCESS_KEY=teste AWS_DEFAULT_REGION=sa-east-1
aws sts get-caller-identity --query Account --output text
```
```text
123456789012
```
(Conta fictícia.) **Cuidado inverso:** se você deixar `AWS_ENDPOINT_URL` exportada, seus comandos "reais" vão para o simulador e **parecem** funcionar. Antes de mexer na AWS de verdade, rode `env | grep AWS_`.

**5. O orçamento, por script.** `scripts/aws/budget.sh` cria um orçamento mensal com alertas (50% e 80% do gasto real e 100% da previsão) para o seu e-mail:
```bash
bash scripts/aws/budget.sh voce@exemplo.com 10      # limite de US$ 10
```
```text
minishop-mensal	10	USD
```
(Esta saída veio do `moto`. Na AWS real, o e-mail precisa ser **confirmado**, e a conta pode exigir que o acesso ao faturamento esteja habilitado para usuários IAM.) Pelo console: *Billing and Cost Management → Budgets → Create budget*, escolha "Zero spend budget" ou "Monthly cost budget". Ative também o **Cost Anomaly Detection** ([documentação](https://docs.aws.amazon.com/cost-management/latest/userguide/manage-ad.html)).

**6. A lista de armadilhas de cobrança.** A documentação oficial ["Understanding unexpected charges"](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/checklistforunwantedcharges.html) tem seções para: uso acima do Free Tier; **instâncias EC2**; **volumes e snapshots EBS**; **endereços IP elásticos**; serviços de armazenamento; **serviços lançados por outros serviços**; **recursos em regiões desativadas**; cobranças após o fechamento da conta. O resumo prático para este módulo:
| Armadilha | Por quê | Defesa |
|---|---|---|
| EC2 esquecida ligada | cobra por hora | destruir no mesmo dia; `verify_clean.sh` |
| **Disco EBS** ou **snapshot** sobrando | sobrevive à instância se `DeleteOnTermination` estiver desligado | conferir volumes e snapshots |
| **IP elástico** sem uso | cobrado por existir | liberar (`release-address`) |
| IPv4 público | cobrado por hora, mesmo em instância gratuita | só quando necessário; destruir |
| RDS "parado" | o armazenamento e os backups continuam cobrando, e a AWS pode religá-lo sozinha após alguns dias (confira o prazo atual na documentação) | **apagar**, não parar |
| Bucket S3 com muitos arquivos/versões | armazenamento e requisições | `rb --force`, conferir versões |
| Serviço criado "por baixo" de outro | ex.: balanceador, NAT Gateway (caro) | listar tudo por tag e por serviço |
| Outra região | você criou lá por engano e não olha | `verify_clean.sh` por região |
| Chave de acesso vazada | terceiros criam recursos na sua conta | sem chaves permanentes; MFA; Git sem segredos |
(Não incluí valores em dólar: eles mudam; use a [calculadora da AWS](https://calculator.aws/) e as páginas de preços na hora.)

## 🧠 Pausa para lógica
**Problema.** Você sobe uma EC2 a US$ 0,012/hora, um RDS a US$ 0,03/hora e paga US$ 0,005/hora por um IPv4 público (**valores fictícios**, só para a conta). Planeja usá-los 6 horas num sábado. (a) Quanto custa esse estudo? (b) Se esquecer tudo ligado por um mês de 30 dias, quanto? (c) Seu orçamento é de US$ 10 com alerta em 80% do gasto real. Em que dia do mês de esquecimento o alerta dispara (começando a contar no dia 1 às 00:00)? (d) Por que isso ainda pode ser tarde demais?

<details><summary>Dica</summary>Some as taxas por hora. 80% de US$ 10 é US$ 8.</details>

<details><summary>Solução comentada</summary>

Taxa total = 0,012 + 0,03 + 0,005 = **US$ 0,047/hora**. (a) 6 × 0,047 = **US$ 0,28**. (b) 24 × 30 × 0,047 = **US$ 33,84**. (c) US$ 8 / 0,047 ≈ 170,2 horas ≈ **7,1 dias**: o alerta dispara no dia 8. (d) Porque o painel de custo tem atraso de horas e o alerta é *depois* do gasto; e porque os US$ 33,84 só são o início se houver discos, snapshots, tráfego de saída ou serviços esquecidos em outras regiões. A defesa real é destruir no mesmo dia e conferir.
</details>

## ⚠️ Erros comuns e boas práticas
| Sintoma / situação | Causa | Solução |
|---|---|---|
| "O alerta não chegou" | E-mail do orçamento não confirmado, ou o gasto ainda não apareceu | Confirmar o e-mail; lembrar do atraso do painel |
| Uso diário com a conta raiz | Comodidade | Identidade de administração com MFA; raiz guardada |
| Chave de acesso no repositório | `.env` commitado | Sem chaves permanentes; `detect-secrets` (módulo 9); se vazou, **desativar a chave na hora** |
| Recurso "sumiu" do console | Região selecionada diferente | Conferir a região no canto superior; `verify_clean.sh` |
| Comando "funciona" mas nada aparece no console | `AWS_ENDPOINT_URL` apontando para o `moto` | `env \| grep AWS_` |
| `AccessDenied` ao ver o faturamento | O acesso de usuários IAM ao faturamento vem desligado | A raiz habilita em *Account → IAM user and role access to Billing* |
| Esquecer em que conta está | Várias contas/perfis | `aws sts get-caller-identity` antes de criar |
| Desligar a EC2 e achar que acabou | Disco, IP e banco continuam | Destruir tudo (aula 08) |

- **Faça o orçamento e o MFA antes de qualquer recurso.** Sem exceção.
- **Tags em tudo** (`Project=minishop-curso`): é como você acha e apaga.
- **Estudo = efêmero:** subir de manhã, destruir à noite, conferir no dia seguinte.
- **Nunca confie só no alerta:** ele chega depois.
- **Segredos nunca no Git** (módulo 9); credenciais temporárias, não chaves permanentes.

## 🧩 Exercícios
**1. Fixação.** (a) EC2, RDS e S3 são IaaS, PaaS ou serviço gerenciado de armazenamento? (b) Região × AZ. (c) O que é seu e o que é da AWS no modelo de responsabilidade compartilhada, num bucket S3? (d) Por que não usar a raiz no dia a dia? (e) O orçamento é um freio ou um alarme?

<details><summary>Solução</summary>

(a) EC2 é IaaS; RDS é PaaS (banco gerenciado); S3 é armazenamento como serviço gerenciado. (b) Região é uma área geográfica; AZ é um data center isolado dentro dela. (c) A AWS cuida da durabilidade e da infraestrutura; você, de quem acessa o bucket e se ele é público. (d) A raiz não pode ser restringida e pode fechar a conta; um vazamento seria total. (e) Um alarme: não desliga nada sozinho.
</details>

**2. Aplicação no projeto MiniShop.**
- [ ] Conta criada (se for criar), com **MFA na raiz** confirmado e **sem chave de acesso na raiz**
- [ ] Identidade de uso diário com MFA e credenciais temporárias (SSO) configuradas
- [ ] `bash scripts/aws/budget.sh seu@email.com 10` e **e-mail de alerta confirmado**; Cost Anomaly Detection ativado
- [ ] `docs/aws.md` com a região escolhida, o nome da conta (não o ID completo em repositório público) e o checklist "antes de criar" preenchido
- [ ] Anotações no `docs/aws.md` do plano da sua conta (gratuito ou pago), a data do fim do crédito e **os tipos de instância/classes de banco que ele aceita** (fonte: a página do Free Tier de hoje)
- [ ] Rodar a CLI contra o `moto` e mostrar `env | grep AWS_` antes e depois de `unset AWS_ENDPOINT_URL`
- [ ] Commit `docs: aws account checklist and budget script`

**3. Desafio (opcional).** Escreva uma tabela com 5 serviços que você usaria no MiniShop e, **só** a partir das páginas de preços oficiais, estime o custo de deixar a arquitetura da aula 07 ligada por um mês. Compare com o resultado da calculadora e explique as diferenças.

## 🎤 Na entrevista
**1. Qual a diferença entre IaaS, PaaS e SaaS?** Quanto o provedor gerencia: em IaaS você cuida do sistema operacional para cima (EC2); em PaaS, só da aplicação e dos dados (RDS, App Runner); em SaaS, só usa o software.

**2. O que é o modelo de responsabilidade compartilhada?** O provedor protege a infraestrutura da nuvem; o cliente protege o que coloca nela: acessos, dados, configuração e, em IaaS, o sistema operacional. Um bucket público é responsabilidade do cliente.

**3. Que cuidados você toma ao criar uma conta de nuvem?** MFA no usuário raiz e nenhuma chave nele; identidade comum com permissões mínimas e credenciais temporárias; orçamento com alertas e detecção de anomalias; tags, região definida, e destruir os recursos de estudo no mesmo dia.

## 📚 Para ir além
- 📄 Documentação oficial: [O que é computação em nuvem](https://aws.amazon.com/what-is-cloud-computing/). Conceitos e modelos de serviço.
- 📄 Documentação oficial: [Regiões e zonas de disponibilidade](https://aws.amazon.com/about-aws/global-infrastructure/regions_az/). Mapa e definições.
- 📄 Documentação oficial: [Modelo de responsabilidade compartilhada](https://aws.amazon.com/compliance/shared-responsibility-model/). A divisão exata de tarefas.
- 📄 Documentação oficial: [AWS Free Tier (contas e créditos)](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/free-tier.html) e [a página de planos](https://aws.amazon.com/free/). **Leia no dia**: os termos mudam.
- 📄 Documentação oficial: [Boas práticas do usuário raiz](https://docs.aws.amazon.com/IAM/latest/UserGuide/root-user-best-practices.html) e [MFA no IAM](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_mfa.html).
- 📄 Documentação oficial: [AWS Budgets](https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-managing-costs.html) e [Understanding unexpected charges](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/checklistforunwantedcharges.html).
- 📄 Documentação oficial: [Guia da AWS CLI v2](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-welcome.html) e [`moto`](https://docs.getmoto.org/en/latest/) (simulador usado nos testes do curso).
- 🎥 Vídeo: sessões "AWS Cloud Practitioner Essentials" (canal oficial *Amazon Web Services*; curso gratuito na AWS Skill Builder): ⚠️ link de vídeo não verificado; procure pelo título.
- 🏋️ Prática extra: leia a página "Understanding unexpected charges" e, para cada seção, escreva um comando da CLI que **listaria** aquele tipo de recurso na sua conta (sem criar nada).

## ✅ Checklist da aula
- [ ] Sei dizer IaaS, PaaS e SaaS e dar um exemplo da AWS de cada
- [ ] Sei o que é região, AZ e responsabilidade compartilhada
- [ ] Criei (ou sei criar) a conta com MFA na raiz e sem chave de acesso nela
- [ ] Orçamento e alertas configurados **antes** de qualquer recurso
- [ ] Sei as armadilhas de cobrança e onde conferir
- [ ] Sei a diferença entre rodar a CLI na AWS e no `moto`
