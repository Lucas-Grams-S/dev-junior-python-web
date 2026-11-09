# 5. RDS (PostgreSQL gerenciado)

> ⏱️ ~1h30 · Módulo 13 · Pré-requisitos: [13.04](04-ec2-security-groups-vpc.md), [3.09 (transações)](../03-banco-de-dados/09-transacoes-acid.md), [8.06 (config por ambiente)](../08-arquitetura/README.md)

> ✅ **Verificação.** Executado: o passo 6 do `provision.sh` **contra o `moto`** (que simula o RDS, sem PostgreSQL de verdade por trás); a leitura de `?sslmode=` na `DATABASE_URL` (código novo, 3 testes, **312 testes** no projeto); a **conexão com e sem TLS** num PostgreSQL 18.6 de contêiner; e **backup e restauração** (`pg_dump`/`pg_restore`) nesse contêiner. **Não executado (sem conta AWS):** um RDS real (tempo de criação, endpoint, certificados da AWS, snapshots, Multi-AZ, versões disponíveis). 💸 RDS gera custo por hora **e** por armazenamento/backup. Código em [`projeto/referencia-api-m13/`](../projeto/referencia-api-m13/README.md).

## 🎯 Objetivos
- Explicar o que o RDS faz por você (e o que **não** faz) em comparação a rodar PostgreSQL na EC2
- Criar um RDS **privado, criptografado e de custo mínimo** pela CLI, com a senha vinda do Parameter Store
- Exigir **TLS** na conexão do Django (`sslmode`) e explicar o erro quando o servidor não oferece
- Fazer e restaurar um **backup lógico** e descrever backups automáticos e *snapshots*
- Listar as **armadilhas de custo** do RDS e como apagá-lo sem deixar rastro

## 🤔 Por que isso importa
O banco é o componente que **não pode ser perdido**. Rodar PostgreSQL "na mão" numa EC2 significa cuidar de atualizações, backups, falhas de disco e recuperação, trabalho de um DBA. O RDS entrega isso pronto, ao custo de dinheiro e de algum controle. Em entrevista: "por que RDS e não PostgreSQL na própria EC2?", "como você faz backup?", "como protege o banco?" são perguntas certas.

## 💡 Intuição (explicação simples)
Ter o próprio banco numa EC2 é **morar em casa própria**: você é dono, mas conserta o telhado, paga a segurança e faz a faxina. O RDS é um **apartamento com condomínio**: o prédio cuida da manutenção, da portaria e do backup do cofre; você paga a taxa e decora o seu cantinho (usuários, esquema, índices). Só **não** pode reformar a estrutura do prédio (acesso ao sistema operacional, extensões não suportadas).

## 🔬 Como funciona por dentro
**O que o RDS gerencia:** provisionar a máquina e o disco; instalar e aplicar *patches* do PostgreSQL (na janela de manutenção); **backups automáticos** com recuperação para um ponto no tempo (PITR) dentro do período de retenção; **snapshots** manuais; monitoramento básico; (opcional) **Multi-AZ**, uma réplica síncrona em outra AZ com troca automática; réplicas de leitura. **O que continua sendo seu:** modelagem, índices, consultas, usuários e senhas, **rede e Security Groups**, criptografia ligada, a decisão de backup e **testar a restauração**, o custo.

**Parâmetros que escolhemos** (todos no `create-db-instance`):
| Parâmetro | Escolha no curso | Por quê |
|---|---|---|
| `--db-instance-class` | `db.t4g.micro` | a menor, para estudo (**confira** se o seu plano a aceita) |
| `--allocated-storage` / `--storage-type` | `20` GB `gp3` | mínimo comum; **armazenamento é cobrado mesmo com a instância desligada** |
| `--storage-encrypted` | ligado | criptografia em repouso; **não dá para ligar depois** em um banco existente (é preciso restaurar de um snapshot copiado criptografado) |
| `--no-publicly-accessible` | sempre | sem IP público; só o SG web alcança (aula 04) |
| `--no-multi-az` | estudo | Multi-AZ dobra o custo; produção real quer |
| `--backup-retention-period` | `1` dia | backups automáticos ligados (0 = desligados); contas de estudo podem exigir valor baixo |
| `--no-deletion-protection` | estudo | permite apagar com o script; **em produção, ligue** |
| `--master-user-password` | vem do Parameter Store | nunca em arquivo nem em argumento fixo do script versionado |
| `--engine-version` | vazio = a padrão da CLI | **depende da região e do tempo**: veja `aws rds describe-db-engine-versions --engine postgres` e escolha a mesma *major* que o seu ambiente de desenvolvimento (PostgreSQL 18 no curso) |
**Sub-rede do banco (*DB subnet group*):** o RDS exige um grupo de **pelo menos duas sub-redes em AZs diferentes**, mesmo no modo de uma AZ só. O script cria um grupo com as sub-redes da VPC padrão.

**Conexão e TLS.** A conexão passa pela rede privada, mas **TLS ainda importa** (defesa em camadas; obrigatório se o tráfego um dia sair da VPC). O libpq/psycopg controla pelo `sslmode`: `disable`, `allow`, `prefer` (padrão: tenta TLS, aceita sem), `require` (exige TLS, sem verificar o certificado), `verify-full` (exige e **verifica o certificado e o nome do servidor**, o ideal, com o certificado raiz da AWS baixado). O Django aceita isso em `OPTIONS`; o `database_from_url` do MiniShop agora lê `?sslmode=` da URL.

**Backups.** Dois mundos: (1) **do RDS** (automáticos + snapshots): restaurar cria uma **nova instância**, com novo endpoint; (2) **lógico** (`pg_dump`/`pg_restore`): portátil, serve para migrar de provedor ou de versão. Ter backup que **nunca foi restaurado** é esperança, não backup (módulo 14 volta ao tema).

**Custo.** Cobra por **hora de instância** + **GB de armazenamento** + backups acima do espaço do banco + tráfego. **Parar** a instância pára só a parte de computação e, no RDS, é temporário (a AWS pode religá-la sozinha após alguns dias; confira o prazo na documentação): para o estudo, **apague**. `--skip-final-snapshot` apaga sem guardar cópia (aceitável no estudo, **perigoso em produção**); os backups automáticos somem junto, a não ser que você peça para mantê-los.

## 🛠️ Exemplo prático
**1. Criar o banco** (passo 6 do `provision.sh`; no `moto`):
```bash
SUBNETS=$(aws ec2 describe-subnets --filters Name=vpc-id,Values="$VPC_ID" --query 'Subnets[].SubnetId' --output text)
aws rds create-db-subnet-group --db-subnet-group-name minishop-db --db-subnet-group-description "MiniShop" --subnet-ids $SUBNETS --tags Key=Project,Value=minishop-curso
aws rds create-db-instance --db-instance-identifier minishop-db --engine postgres \
  --db-instance-class db.t4g.micro --allocated-storage 20 --storage-type gp3 --storage-encrypted \
  --master-username minishop --master-user-password "$DB_PASSWORD" --db-name minishop \
  --db-subnet-group-name minishop-db --vpc-security-group-ids "$SG_DB" --no-publicly-accessible --no-multi-az \
  --backup-retention-period 1 --no-deletion-protection --tags Key=Project,Value=minishop-curso
aws rds wait db-instance-available --db-instance-identifier minishop-db     # 💸 na AWS real, vários minutos
DB_HOST=$(aws rds describe-db-instances --db-instance-identifier minishop-db --query 'DBInstances[0].Endpoint.Address' --output text)
aws ssm put-parameter --name /minishop/DATABASE_URL --type SecureString --value "postgres://minishop:${DB_PASSWORD}@${DB_HOST}:5432/minishop"
```
```text
db.t4g.micro	False	True	False        ← classe, PubliclyAccessible, StorageEncrypted, MultiAZ (saída do simulador)
Endpoint do banco: minishop-db.aaaaaaaaaa.sa-east-1.rds.amazonaws.com        ← endereço FICTÍCIO do simulador
```
A senha é gerada com `secrets.token_urlsafe(24)`, enviada ao RDS e **gravada só no Parameter Store** (como `SecureString`); a `DATABASE_URL` completa também fica lá, e a instância a lê no boot (aula 08). `token_urlsafe` produz só caracteres seguros em URL (letras, números, `-` e `_`), o que evita o erro clássico de uma senha com `@` ou `/` quebrando a URL. (Já os testes do projeto cobrem o caso de senha com caracteres especiais decodificados: `test_postgres_decodifica_senha_com_caracteres_especiais`.)

**2. TLS na `DATABASE_URL`.** A mudança no `config/envconf.py` (módulo 13): aceitar só opções conhecidas, e **recusar** as desconhecidas, para que um erro de digitação não vire "sem TLS" em silêncio:
```python
permitidas = {"sslmode", "sslrootcert", "connect_timeout"}
opcoes = {k: v for k, v in parse_qsl(u.query) if k in permitidas}
desconhecidas = {k for k, _ in parse_qsl(u.query)} - permitidas
if desconhecidas:
    raise ImproperlyConfigured(f"DATABASE_URL com parâmetros não suportados: {sorted(desconhecidas)}")
# ... "OPTIONS": opcoes
```
```text
tests/test_envconf.py ............   12 passed        (3 testes novos: sslmode lido, OPTIONS vazio sem query, parâmetro desconhecido rejeitado)
```
Teste real contra um PostgreSQL 18.6 **de contêiner** (que, por padrão, **não** tem TLS ligado: `show ssl` → `off`):
```text
DATABASE_URL=postgres://m:x@127.0.0.1:55432/m                       → conectou; TLS em uso: False
DATABASE_URL=postgres://m:x@127.0.0.1:55432/m?sslmode=require        → ERRO: connection failed: ... server does not support SSL, but SSL was required
```
Esse é exatamente o comportamento desejado em produção: **a aplicação se recusa a falar sem TLS** (ela falha alto em vez de cair no texto puro). Na AWS, o RDS oferece TLS; use `?sslmode=require` e, para o ideal, `verify-full` com `sslrootcert` apontando para o pacote de certificados da AWS (consulte a documentação do RDS; **não executei**). Por isso o `provision.sh` guarda a URL **sem** `sslmode` por enquanto, e a aula 08 mostra acrescentar `?sslmode=require` depois que você confirmar que o seu RDS responde com TLS (um passo manual, para você não ficar sem acesso por engano).

**3. Backup lógico e restauração** (num PostgreSQL 18.6 de contêiner; os comandos são os mesmos contra o RDS, de dentro da EC2 ou por túnel):
```bash
pg_dump -U postgres -Fc -d minishop -f /tmp/minishop.dump           # formato "custom": compacto, restauração seletiva
dropdb minishop && createdb minishop
pg_restore -U postgres -d minishop --no-owner /tmp/minishop.dump
```
```text
antes: 1000
dump: 6288 bytes
depois do restore: 1000
```
`--no-owner` evita erros quando o dono dos objetos não existe no destino (comum entre ambientes). Contra o RDS: `pg_dump "postgres://minishop:SENHA@ENDPOINT:5432/minishop?sslmode=require" -Fc -f minishop.dump` (de uma máquina que consiga alcançar o banco; lembre-se: ele é privado). O restore **testado** (contagem igual) é o que torna o backup um backup.

**4. Migrações e dados iniciais no RDS.** O serviço `migrate` do Compose (aula 07) roda `python manage.py migrate` contra o RDS no deploy. **Não** rode o `seed` em produção (ele recusa: `ALLOW_SEED = DEBUG`, módulo 9).

## 🧠 Pausa para lógica
**Problema.** Um RDS `db.t4g.micro` custa US$ 0,02/hora e 20 GB de `gp3` custam US$ 0,12 por GB-mês (**valores fictícios**). (a) Qual o custo de deixá-lo ligado por 30 dias? (b) E "parado" durante 25 desses dias (suponha que só a computação pára)? (c) E se você o **apagar** no dia 5, sem snapshot? (d) Por que "parar" não é uma estratégia de economia confiável para o estudo?

<details><summary>Dica</summary>Separe computação (por hora) de armazenamento (por GB-mês). Pense no que acontece depois de alguns dias parado.</details>

<details><summary>Solução comentada</summary>

(a) Computação: 24 × 30 × 0,02 = **US$ 14,40**; armazenamento: 20 × 0,12 = **US$ 2,40**; total **US$ 16,80**. (b) Computação só nos 5 dias ligado: 24 × 5 × 0,02 = 2,40; armazenamento ainda os 30 dias: 2,40 → **US$ 4,80**. (c) Computação 5 dias = 2,40; armazenamento ~5/30 de 2,40 = 0,40 → **cerca de US$ 2,80**; depois disso, **zero**. (d) Porque o armazenamento e os backups continuam cobrando, a instância pode ser **religada automaticamente** pela AWS depois de alguns dias, e você esquece. Para estudo: apague; recrie quando precisar (e use o dump para repovoar).
</details>

## ⚠️ Erros comuns e boas práticas
| Sintoma / mensagem | Causa | Solução |
|---|---|---|
| `password authentication failed for user "minishop"` | Senha diferente da usada na criação | Reconferir o Parameter Store; **não** misturar volumes antigos (aula 11.04) |
| `connection timed out` ao banco | SG sem a regra do SG web, ou banco em outra VPC | Regra `5432` com origem = SG web; mesma VPC |
| `could not translate host name` | Endpoint errado/ainda criando | `rds wait db-instance-available`; copiar o endpoint certo |
| `server does not support SSL, but SSL was required` | `sslmode=require` num servidor sem TLS | No RDS há TLS; em contêiner local, remova o `sslmode` |
| `DATABASE_URL com parâmetros não suportados: ['ssl_mode']` | Erro de digitação | `sslmode` (sem `_`); a falha é de propósito |
| `DBSubnetGroupDoesNotCoverEnoughAZs` | Menos de 2 AZs no grupo | Sub-redes de pelo menos duas AZs |
| `InvalidParameterCombination` (classe/versão/armazenamento) | Combinação não suportada na região/plano | `describe-orderable-db-instance-options`; ler o erro |
| Banco criado sem criptografia | Esqueceu o `--storage-encrypted` | Não dá para ligar depois: recriar |
| Conta com cobrança de RDS que "não existe" | Banco em outra região, parado ou snapshot manual | `verify_clean.sh` (RDS + snapshots), por região |
| `pg_restore: error: could not execute query: role "x" does not exist` | Dono dos objetos inexistente | `--no-owner` (e `--no-privileges` se preciso) |
- **O banco nunca tem IP público**; acesso administrativo por túnel autenticado.
- **TLS e menor privilégio no banco** (um usuário da aplicação sem `SUPERUSER`; o `master` só para administração; módulo 9.07).
- **Teste a restauração** pelo menos uma vez; anote o tempo.
- **Proteção contra exclusão ligada em produção**; desligada no estudo, sabendo disso.
- **Mesma *major* de PostgreSQL** em desenvolvimento, testes (CI) e produção.

## 🧩 Exercícios
**1. Fixação.** (a) Três coisas que o RDS faz por você e três que continuam sendo suas. (b) Por que o grupo de sub-redes exige duas AZs? (c) `require` × `verify-full`. (d) Por que `--no-publicly-accessible`? (e) Por que não basta "parar" o RDS?

<details><summary>Solução</summary>

(a) Faz: backups automáticos, patches, monitoramento/alta disponibilidade opcional. Seu: modelagem/índices, usuários e redes, testar restauração e custo. (b) Para permitir a troca de AZ (Multi-AZ) e a recuperação, mesmo que a instância use uma só. (c) `require` cifra mas não verifica o servidor; `verify-full` também verifica o certificado e o nome (protege contra interceptação). (d) Sem IP público ele só é alcançável de dentro da rede, por quem o SG permitir. (e) Armazenamento e backups cobram, e o RDS pode religar sozinho.
</details>

**2. Aplicação no projeto MiniShop.**
- [ ] Executar o passo 6 no `moto` e mostrar (`describe-db-instances`) classe, `PubliclyAccessible=False`, `StorageEncrypted=True`, `MultiAZ=False`
- [ ] `database_from_url` com `?sslmode=` e **3 testes** (leitura, `OPTIONS` vazio, rejeição de parâmetro desconhecido); suíte verde
- [ ] A prova do `sslmode=require` falhando num PostgreSQL local sem TLS (mensagem colada em `docs/aws.md`)
- [ ] Backup lógico e restauração num contêiner, **com a contagem de linhas antes e depois** e o tempo
- [ ] Uma tabela de custos **hipotética** do RDS (computação + armazenamento + backup), usando só a calculadora oficial, com as premissas
- [ ] `docs/aws.md` com "como acessar o banco de produção" (túnel, nunca IP público) e "como restaurar"
- [ ] Commit `feat(aws): rds provisioning, sslmode support and backup notes`

**3. Desafio (opcional).** Escreva um teste de integração (pytest) que cria um usuário de banco **somente com os privilégios que a aplicação precisa** (`CONNECT`, `USAGE`, `SELECT/INSERT/UPDATE/DELETE` nas tabelas, sem `CREATE` nem `SUPERUSER`) num PostgreSQL de contêiner e roda a suíte de API com ele, descobrindo se as migrações exigem um usuário mais forte (e como separar os dois: um para `migrate`, outro para a aplicação).

## 🎤 Na entrevista
**1. Por que usar RDS em vez de instalar PostgreSQL numa EC2?** O RDS automatiza provisionamento, patches, backups com recuperação para um ponto no tempo, monitoramento e alta disponibilidade opcional, reduzindo o trabalho operacional e o risco de perda de dados; em troca, custa mais e dá menos controle sobre o sistema operacional.

**2. Como você protege o banco de uma aplicação em nuvem?** Sem IP público, em sub-rede/SG que só aceita a aplicação, TLS na conexão, criptografia em repouso, usuários com menor privilégio, senha em gerenciador de segredos, backups testados e proteção contra exclusão.

**3. Como você faz backup e restauração?** Backups automáticos e snapshots do RDS (a restauração cria nova instância) e dumps lógicos (`pg_dump -Fc`/`pg_restore`) para portabilidade; o importante é testar a restauração periodicamente e medir o tempo.

## 📚 Para ir além
- 📄 Documentação oficial: [Amazon RDS para PostgreSQL](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_PostgreSQL.html). Versões, extensões, parâmetros e limites.
- 📄 Documentação oficial: [RDS em uma VPC](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_VPC.WorkingWithRDSInstanceinaVPC.html) e [Backups automáticos](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_WorkingWithAutomatedBackups.html). Sub-redes, retenção e PITR.
- 📄 Documentação oficial: [Apagar uma instância](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_DeleteInstance.html). Snapshot final e backups automáticos.
- 📄 Documentação oficial: [Preços do RDS](https://aws.amazon.com/rds/pricing/) e [Calculadora](https://calculator.aws/).
- 📄 Documentação: [PostgreSQL — `pg_dump`](https://www.postgresql.org/docs/18/app-pgdump.html), [`pg_restore`](https://www.postgresql.org/docs/18/app-pgrestore.html) e [conexão com SSL](https://www.postgresql.org/docs/18/libpq-ssl.html). Os modos de `sslmode`.
- 🏋️ Prática extra: restaure o dump numa **segunda** versão do contêiner PostgreSQL e anote o que muda ao trocar de versão *major* (por isso o dump lógico é a ferramenta de migração).

## ✅ Checklist da aula
- [ ] Sei o que o RDS gerencia e o que continua comigo
- [ ] O RDS do curso é privado, criptografado, de custo mínimo e com senha no Parameter Store
- [ ] A `DATABASE_URL` aceita `sslmode` e rejeita parâmetros desconhecidos (3 testes)
- [ ] Fiz um backup lógico e **restaurei** conferindo as linhas
- [ ] Sei por que apagar é melhor que parar e o que cobra no RDS
