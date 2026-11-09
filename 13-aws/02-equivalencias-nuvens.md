# 2. Equivalências AWS ↔ Azure ↔ GCP (conceito, sem prática)

> ⏱️ ~1h30 · Módulo 13 · Pré-requisitos: [13.01](01-conceitos-conta-mfa-custos.md)

> ✅ **Verificação.** Aula **conceitual, sem prática** (como o plano previa): nada foi executado. A tabela de equivalências foi montada a partir do que eu usei no módulo (AWS) e do conhecimento geral dos serviços das outras duas nuvens; **as correspondências são aproximadas** e as comparações oficiais da Microsoft e do Google (links abaixo, conferidos com HTTP 200 em 2026-11-09) são a fonte de verdade. Não criei contas nem recursos em Azure ou GCP.

## 🎯 Objetivos
- Mapear os serviços usados pelo MiniShop na AWS para os equivalentes da **Azure** e do **Google Cloud**
- Explicar que os **conceitos se repetem** e que os **nomes e detalhes mudam**
- Identificar pontos de **dependência do provedor** (*lock-in*) e como reduzi-los
- Responder em entrevista "eu só conheço AWS, e se a vaga for Azure/GCP?"

## 🤔 Por que isso importa
O mercado usa as três nuvens, e a vaga raramente casa com a que você estudou. O que **transfere** é o raciocínio: identidade e permissões mínimas, rede privada, banco gerenciado, armazenamento de objetos, logs e custos. Quem entende o *porquê* de cada peça troca de nuvem em semanas; quem decorou cliques da AWS recomeça do zero.

## 💡 Intuição (explicação simples)
Operadoras de celular: todas vendem **chamadas, dados e SMS**, mas cada uma dá nomes diferentes aos planos, cobra de um jeito e tem um aplicativo próprio. Quem entende "franquia de dados" e "roaming" se vira em qualquer uma. Nas nuvens, o "plano" é o serviço: máquina virtual, banco, armazenamento.

## 🔬 Como funciona por dentro
**O que o MiniShop usa e como isso se chama em cada nuvem**
| Necessidade | AWS (módulo 13) | Azure | Google Cloud |
|---|---|---|---|
| Máquina virtual | **EC2** | Virtual Machines | Compute Engine |
| Contêineres gerenciados | ECS, App Runner (EKS = Kubernetes) | Container Apps, Container Instances (AKS) | Cloud Run (GKE) |
| Registro de imagens | **ECR** | Container Registry (ACR) | Artifact Registry |
| Banco relacional gerenciado | **RDS** (PostgreSQL) | Azure Database for PostgreSQL | Cloud SQL (PostgreSQL) |
| Armazenamento de objetos | **S3** | Blob Storage | Cloud Storage |
| Rede privada virtual | **VPC**, subnets, security groups | Virtual Network, Network Security Groups | VPC, regras de firewall |
| Identidade e permissões | **IAM** (usuários, papéis, políticas) | Microsoft Entra ID + RBAC | Cloud IAM |
| Segredos | Parameter Store, **Secrets Manager** | Key Vault | Secret Manager |
| Logs e métricas | **CloudWatch** | Azure Monitor | Cloud Logging / Monitoring |
| Funções sem servidor | Lambda | Functions | Cloud Functions / Cloud Run |
| Fila / mensageria | SQS, SNS | Service Bus, Event Grid | Pub/Sub |
| Balanceador | ELB (ALB) | Load Balancer / Application Gateway | Cloud Load Balancing |
| Infra como código nativa | CloudFormation, CDK | ARM / Bicep | Deployment Manager (vem sendo substituído) |
| Cache Redis gerenciado | ElastiCache | Azure Cache for Redis | Memorystore |
**Como ler a tabela.** (1) As linhas são *aproximadas*: "Cloud Run" não é igual a "App Runner" em limites, preços e modelo de escala. (2) O **conceito** é o que transfere (nesta tabela: máquina, contêiner, banco, objeto, rede, identidade, segredo, log). (3) O que **não** transfere: nomes de console, o formato de políticas (JSON do IAM × atribuições RBAC), limites, preços, regiões, a CLI (`aws` × `az` × `gcloud`).

**Três diferenças conceituais que valem saber**
- **Identidade.** A AWS tem a *conta* como fronteira e o IAM dentro dela; a Azure organiza em *assinaturas* sob um diretório (Entra ID); o Google organiza em *projetos* sob uma organização. O princípio de menor privilégio e o uso de **papéis** em vez de chaves permanentes valem nas três.
- **Rede.** Na AWS, a VPC é regional e as sub-redes são de uma AZ; no Google, a VPC é global. As consequências aparecem em desenho de redes, não na aula de hoje.
- **Faturamento.** Nomes e granularidade das cobranças diferem; as armadilhas (IP público, disco órfão, saída de dados, serviços esquecidos) são as mesmas.

**Lock-in (dependência do provedor).** Quanto mais você usa serviços proprietários (Lambda com gatilhos próprios, DynamoDB, SQS), mais caro é sair. Como reduzir para um júnior: (1) **contêineres** (Docker) para a aplicação; (2) **PostgreSQL padrão** (RDS, Cloud SQL e Azure Database falam o mesmo protocolo); (3) armazenamento de objetos atrás de uma interface (`django-storages` aceita S3, Azure Blob e Google Cloud Storage); (4) configuração por variáveis de ambiente (12 fatores); (5) infraestrutura como código com ferramenta neutra (Terraform), **só mencionada** neste curso. Não existe portabilidade grátis: a decisão é conhecer o custo da saída antes de entrar.

**Multi-nuvem** é raro e caro para quem está começando. Para um projeto pequeno, escolha **uma**, pelo ecossistema da empresa, pelos créditos e pela documentação que você entende.

## 🛠️ Exemplo prático
(Aula sem prática. O exercício é de mapeamento.) Exemplo resolvido para **um** componente, o armazenamento de mídia:
| | AWS | Azure | Google Cloud |
|---|---|---|---|
| Serviço | S3 | Blob Storage | Cloud Storage |
| Unidade | *bucket* + objetos (`products/cas-049.png`) | *storage account* + *container* + blobs | *bucket* + objetos |
| Acesso privado temporário | URL pré-assinada (SigV4) | SAS (Shared Access Signature) | URL assinada |
| No Django | `storages.backends.s3.S3Storage` | `storages.backends.azure_storage.AzureStorage` | `storages.backends.gcloud.GoogleCloudStorage` |
| Identidade da aplicação | papel da instância (instance profile) | identidade gerenciada | conta de serviço |
Repare que a **aplicação** mudaria apenas a classe de armazenamento e as variáveis; o conceito (bucket privado + URL temporária + identidade sem chave no código) é o mesmo. Essa é a razão do `STORAGES` por variável de ambiente que você verá na aula 06.

## 🧠 Pausa para lógica
**Problema.** Sua empresa pensa em trocar de nuvem. Você lista as dependências do MiniShop: (A) código Django em Docker; (B) PostgreSQL via `DATABASE_URL`; (C) uploads em S3 via `django-storages`; (D) fila no Redis (Celery); (E) 40 funções Lambda acionadas por eventos do S3 e do SQS. Classifique cada item de "portável com pouco esforço" a "preso ao provedor" e diga por onde começaria a migração.

<details><summary>Dica</summary>Pergunte: o que muda se eu trocar só o endereço e as credenciais? O que exige reescrever?</details>

<details><summary>Solução comentada</summary>

Mais portáveis: **(A)** contêiner, roda em qualquer lugar; **(B)** PostgreSQL padrão, troca a URL (e migra os dados com `pg_dump`/`pg_restore`); **(D)** Redis é padrão (troca o endereço). **(C)** exige trocar a classe de armazenamento e **migrar os objetos** (esforço médio, interface única pelo `django-storages`). **(E)** é o mais preso: gatilhos de eventos e o modelo de execução são do provedor; exigiria reescrita para o equivalente da outra nuvem (ou para uma fila neutra). Começaria por A, B e D (baixo risco), depois C, e deixaria E para o fim, medindo antes se compensa. O custo oculto costuma ser **dados e rede** (levar terabytes de uma nuvem a outra é cobrado).
</details>

## ⚠️ Erros comuns e boas práticas
| Erro | Por quê | Melhor |
|---|---|---|
| "Aprendi AWS = aprendi nuvem" ou "AWS é inferior" | Confundir nome de serviço com conceito | Estudar o conceito e ter um mapa de equivalências |
| Escolher serviço proprietário "porque é fácil" sem medir a saída | Lock-in silencioso | Contêiner + PostgreSQL + interface de armazenamento |
| Copiar uma política IAM para o Azure/GCP | Modelos diferentes de permissão | Ler o modelo de cada nuvem |
| Comparar preços só de instância | O custo real inclui disco, rede, IP, saída | Calculadora do provedor com a arquitetura inteira |
| Multi-nuvem "por segurança" no projeto pequeno | Complexidade multiplicada | Uma nuvem bem feita, com backup e portabilidade razoável |

- **Documente a decisão** (um ADR curto: por que AWS, quais alternativas, o custo de sair).
- **Prefira padrões abertos** (PostgreSQL, S3-compatível, OCI, OpenTelemetry) quando custam pouco.
- **Verifique nomes e preços na fonte**, não em tabelas de blog (inclusive esta).

## 🧩 Exercícios
**1. Fixação.** (a) Cite o equivalente do S3 na Azure e no Google Cloud. (b) O que é lock-in? (c) Três decisões que reduzem o lock-in no MiniShop. (d) O que **não** transfere entre nuvens?

<details><summary>Solução</summary>

(a) Blob Storage; Cloud Storage. (b) Dependência de recursos proprietários que tornam a saída cara. (c) Docker, PostgreSQL via `DATABASE_URL` e `django-storages` com configuração por ambiente. (d) Nomes e telas, formato de políticas, limites, preços, CLI.
</details>

**2. Aplicação no projeto MiniShop.**
- [ ] `docs/nuvens.md` com a tabela de equivalências **dos componentes do MiniShop** (web, worker, fila, banco, mídia, segredos, logs, rede, identidade, registro de imagens), preenchida por você a partir das **páginas oficiais de comparação** (links abaixo), marcando o que você **não** soube preencher
- [ ] Um ADR curto (`docs/adr/00X-nuvem.md`): por que AWS no curso, alternativas consideradas e o custo de sair de cada dependência
- [ ] Lista das dependências proprietárias hoje no MiniShop (resposta esperada: quase nenhuma, e por quê)
- [ ] Commit `docs: cloud equivalence table and adr`

**3. Desafio (opcional).** Escolha a nuvem de uma vaga real (veja `00-guia/o-que-o-mercado-pede.md`) e escreva, em uma página, como você levaria o MiniShop para ela, serviço por serviço, e o que precisaria aprender primeiro.

## 🎤 Na entrevista
**1. Você só conhece AWS. E se a vaga for em Azure ou GCP?** Os conceitos são os mesmos (máquinas, rede privada, banco gerenciado, objetos, identidade com menor privilégio, logs, custos); mudam nomes, console e detalhes. Eu uso um mapa de equivalências, começo pela documentação e por um projeto pequeno, e já mantenho minha aplicação portável (contêiner, PostgreSQL, configuração por ambiente).

**2. O que é lock-in e como evitar?** Dependência de serviços proprietários que encarece a saída. Reduz-se usando contêineres, padrões abertos (PostgreSQL, S3-compatível), camadas de abstração finas e infraestrutura como código; mas é um equilíbrio: serviços gerenciados economizam trabalho, e a decisão deve ser consciente.

**3. Vale a pena multi-nuvem?** Raramente para times pequenos: dobra a complexidade operacional. Faz sentido por exigência regulatória, de cliente ou de resiliência em larga escala.

## 📚 Para ir além
- 📄 Comparação oficial: [Microsoft — serviços Azure para profissionais AWS](https://learn.microsoft.com/en-us/azure/architecture/aws-professional/services). Tabela e diferenças conceituais (em inglês).
- 📄 Comparação oficial: [Google Cloud — comparação AWS, Azure e GCP](https://cloud.google.com/docs/get-started/aws-azure-gcp-service-comparison). Serviço por serviço (em inglês).
- 📄 Documentação: [`django-storages`](https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html). Backends de S3, Azure e GCS.
- 📄 Documentação: [Well-Architected (AWS)](https://aws.amazon.com/architecture/well-architected/). Pilares que valem para qualquer nuvem: segurança, confiabilidade, custo, desempenho, excelência operacional, sustentabilidade.
- 📄 Documentação: [Terraform — introdução](https://developer.hashicorp.com/terraform/intro) e [AWS CDK](https://docs.aws.amazon.com/cdk/v2/guide/home.html). Infraestrutura como código (só leitura nesta aula).
- 🏋️ Prática extra: para três serviços da tabela, abra a página de preços de cada nuvem e anote **a unidade cobrada** (hora, GB, requisição). Compare as unidades, não os valores.

## ✅ Checklist da aula
- [ ] Sei mapear os componentes do MiniShop para as três nuvens
- [ ] Sei o que muda e o que se repete entre elas
- [ ] Sei o que é lock-in e três formas de reduzi-lo
- [ ] Escrevi o ADR da escolha de nuvem
