# 4. Performance (consultas lentas) e backups

> ⏱️ ~1h30 · Módulo 14 · Pré-requisitos: [14.03](03-cache-redis.md), [3.08 (constraints, índices e `EXPLAIN`)](../03-banco-de-dados/08-constraints-indices-explain.md), [13.05 (RDS, backup e restauração)](../13-aws/05-rds-postgres.md)

> ✅ **Verificação.** Executado em 2026-11-09 com **PostgreSQL 18.6 (contêiner), 200 064 produtos** (180 061 ativos) e Django: `EXPLAIN (ANALYZE)` de cada consulta **antes e depois** de índices, o `pg_stat_statements` e o log de consultas lentas (`log_min_duration_statement`), o índice novo no projeto (migração `0003`; suíte de **341 testes**, 338 + 4 pulados em PostgreSQL), e os **scripts de backup e de teste de restauração** (`scripts/prod/`) com `pg_dump`/`pg_restore` do PostgreSQL 18, inclusive com arquivos **truncados, adulterados e com checksum "consertado"**. **Não executado:** `pg_basebackup`/arquivamento de WAL (recuperação para um ponto no tempo), restauração de um snapshot do RDS, envio ao S3 pelo `backup.sh` (`BACKUP_S3_URI`), agendamento (`cron`/timer) e `pg_stat_statements` no RDS. Os tempos são desta máquina, com a tabela em memória (cache quente). Código em [`projeto/referencia-api-m14/`](../projeto/referencia-api-m14/README.md).

## 🎯 Objetivos
- **Achar** as consultas lentas com evidência (log de lentas, `pg_stat_statements`), em vez de adivinhar
- Ler um `EXPLAIN (ANALYZE)` e relacionar **plano × índice × tempo**
- Criar o **índice certo** para a listagem do catálogo e **provar** o ganho (e onde ele **não** ajuda)
- Entender o custo da **paginação por OFFSET** e a alternativa por **cursor/keyset**
- Fazer **backup** consistente, **verificar** sua integridade e **testar a restauração** medindo o tempo (RTO)

## 🤔 Por que isso importa
"O site está lento" raramente se resolve com "adicione cache": quase sempre é **uma ou duas consultas** que você consegue achar e consertar em minutos, se souber onde olhar. E o outro lado da moeda: o dia em que o banco se perde. Backup que nunca foi restaurado é **esperança**, não backup. Em entrevista: "como você acha uma consulta lenta?" e "qual seu RPO e RTO?" medem se você já operou um sistema.

## 💡 Intuição (explicação simples)
Procurar uma palavra num livro de 200 mil páginas. **Sem índice**, você lê página a página (varredura sequencial). **Com índice remissivo**, vai direto às páginas certas. Mas um índice remissivo ordenado por "nome do produto" só ajuda se a sua pergunta for "me dê os 20 primeiros por nome"; para "contar quantos há" ou "achar quem contém `a1b2c3` no meio da palavra", o índice comum não serve (precisa de um índice **de outro tipo**, como o de trigramas). E pular para a página 9000 de uma lista paginada obriga a **contar** 180 mil linhas antes de mostrar as 20 seguintes, a menos que você use um **marcador de página** (o cursor): "continue depois do item X".

## 🔬 Como funciona por dentro
**Método para achar o que está lento** (nesta ordem):
1. **Meça de fora:** métricas por rota (p95/p99 do histograma, aula 02) dizem *qual endpoint*.
2. **Meça de dentro:** o banco diz *qual consulta*: (a) **log de consultas lentas** (`log_min_duration_statement = 50` registra tudo que passa de 50 ms, com o SQL); (b) a extensão **`pg_stat_statements`** acumula, por consulta normalizada, `calls`, `total_exec_time` e `mean_exec_time`. **Ordene pelo tempo TOTAL**, não pela média: a consulta de 10 ms chamada 10 mil vezes pesa mais que a de 1 s chamada duas vezes.
3. **Entenda o plano:** `EXPLAIN (ANALYZE, BUFFERS)` *executa* a consulta e mostra o plano real: `Seq Scan` (lê tudo), `Index Scan`/`Index Only Scan` (usa índice), `Sort` (e se foi em memória ou em disco: `external merge Disk`), tempos e linhas reais × estimadas. Cuidado: `ANALYZE` **executa de verdade** (um `UPDATE` seria aplicado; use dentro de uma transação com `ROLLBACK`).
4. **Corrija com o mínimo:** índice, reescrita, paginação melhor, ou (por último) cache.
5. **Prove:** meça de novo.

**Índices (recapitulando o módulo 3, agora com números).** Um índice B-tree em `(is_active, name)` guarda os pares **já ordenados**: a consulta `WHERE is_active ORDER BY name LIMIT 20` lê as 20 primeiras entradas e para. Custos: ocupa espaço, **torna as escritas mais lentas** (cada `INSERT/UPDATE` atualiza o índice), e só vale se a consulta for frequente. **A ordem das colunas importa:** `(is_active, name)` atende "filtra por `is_active` e ordena por `name`", mas **não** "ordena por `name` sem filtro" (o staff, que lista inativos também, não aproveita). Índices que **não** ajudam: `COUNT(*)` (precisa contar), `LIKE '%texto%'` (curinga no começo).

**Paginação.** `OFFSET N` obriga o banco a **produzir e descartar N linhas** antes de devolver as seguintes: o custo cresce com N (página 9000 = descartar 180 mil). **Keyset/cursor** (`WHERE name > último_visto ORDER BY name LIMIT 20`) usa o índice para **pular direto** e tem custo constante, mas não permite "ir para a página 50". O DRF tem `CursorPagination` (o projeto já usa em outro ponto). Há ainda o `COUNT(*)` que a paginação por páginas faz em **toda** requisição.

**Backup: vocabulário que cai em entrevista**
| Termo | Significado | No MiniShop |
|---|---|---|
| **RPO** (*recovery point objective*) | quanto de dado você aceita perder (tempo entre o último backup e a falha) | backup diário → até 24 h; RDS com PITR → minutos |
| **RTO** (*recovery time objective*) | em quanto tempo você volta ao ar | **medido** pelo teste de restauração |
| **Backup lógico** (`pg_dump`) | exporta SQL/objetos; portável entre versões | `-Fc` (formato "custom", comprimido, restauração seletiva) |
| **Backup físico** (`pg_basebackup` + WAL) | cópia dos arquivos + log de transações; permite voltar a um **instante** (PITR) | o RDS faz por você (automático) |
| **Regra 3-2-1** | 3 cópias, 2 mídias diferentes, 1 fora do local | dump local + S3 em outra conta/região |
- **Consistência.** O `pg_dump` lê tudo dentro de **um único instantâneo** (MVCC): mesmo com o site escrevendo, o dump é consistente em um instante, sem bloquear escritas.
- **Um backup só vale se for restaurado.** O teste de restauração restaura num banco **temporário**, confere integridade e conteúdo, mede o tempo e apaga o temporário.
- **Backups contêm dados pessoais:** proteja-os como o banco (cifre, restrinja acesso, defina retenção, e lembre-se da LGPD: um titular que pede eliminação continua nos backups até eles expirarem, o que a política de retenção deve prever).
- O **S3** tem versionamento para a mídia (aula 13.06); backups do banco e da mídia são **dois** planos.

## 🛠️ Exemplo prático
**1. Achar as consultas: log de lentas e `pg_stat_statements`.** O contêiner do PostgreSQL de teste, com as duas coisas ligadas:
```bash
docker run -d --name lab14-pg -e POSTGRES_USER=m -e POSTGRES_PASSWORD=x -e POSTGRES_DB=m -p 127.0.0.1:55434:5432 postgres:18 \
  -c shared_preload_libraries=pg_stat_statements -c log_min_duration_statement=50 -c pg_stat_statements.track=all
docker exec lab14-pg psql -U m -d m -c "create extension pg_stat_statements"
```
Com 200 064 produtos, simulei tráfego: 45 requisições (30 na página 1, 5 na página 9000, 5 de busca, 5 ordenadas por preço), sem cache. Consulta ao `pg_stat_statements` **ordenada pelo tempo total**:
```sql
select calls, round(total_exec_time::numeric,0) as total_ms, round(mean_exec_time::numeric,2) as media_ms, left(query,110)
from pg_stat_statements where query ilike '%catalog_product%' and query not ilike '%pg_stat_statements%' order by total_exec_time desc limit 5;
```
```text
calls | total_ms | media_ms | consulta
   40 |      447 |    11.19 | SELECT COUNT(*) AS "__count" FROM "catalog_product" WHERE "catalog_product"."is_active"
    5 |      421 |    84.18 | SELECT "catalog_product"."id", ... (a página 9000, com OFFSET)
    5 |      309 |    61.72 | SELECT COUNT(*) ... WHERE (is_active AND (UPPER(name) LIKE UPPER('%a1b2c3%') OR ...    (a busca)
    5 |      140 |    28.06 | SELECT ... ORDER BY price DESC LIMIT 20
   30 |        1 |     0.04 | SELECT ... (a página 1: já com o índice da seção 3)
```
**A lição está na primeira linha:** a consulta que **mais** consome o banco não é a "lenta" (a página funda, 84 ms), é o **`COUNT(*)`** de 11 ms, chamada em **toda** listagem (40 vezes = 447 ms), porque a paginação por páginas precisa do total. Quem olhasse só a média acharia a página funda; quem olha o total vê que o `COUNT` é o maior custo agregado. E o log de lentas mostra as mesmas culpadas, com o SQL completo e o tempo:
```text
LOG:  duration: 63.001 ms  statement: SELECT COUNT(*) AS "__count" FROM "catalog_product" WHERE ("catalog_product"."is_active" AND (UPPER("catalog_product"."name"::text) LIKE UPPER('%a1b2c3%') OR ...
LOG:  duration: 61.312 ms  statement: ...
```
(No RDS, o equivalente é o parâmetro `log_min_duration_statement` no *parameter group*, enviado ao CloudWatch Logs, e o *Performance Insights*; **não executei** nenhum dos dois.)

**2. Ler o plano e provar o índice.** As mesmas quatro consultas, `EXPLAIN (ANALYZE, TIMING OFF)`, **sem** e **com** o índice `CREATE INDEX product_active_name_idx ON catalog_product (is_active, name)`; "Execution Time" real:
| Consulta (SQL) | Sem índice | Com índice | O plano mudou para |
|---|---|---|---|
| Q1 página 1: `WHERE is_active ORDER BY name LIMIT 20` | **20,0 ms** | **0,044 ms** | `Sort` (top-N heapsort sobre 180 mil linhas) → `Index Scan` |
| Q2 página 9000: `... LIMIT 20 OFFSET 179980` | 407,7 ms | 410,4 ms | **continua `Sort` em disco** (`external merge Disk: 10424kB`) |
| Q3 `COUNT(*) WHERE is_active` | 11,6 ms | 11,1 ms | `Parallel Seq Scan` → `Index Only Scan`: **sem ganho** |
| Q4 busca `UPPER(name) LIKE UPPER('%a1b2c3%') OR ...` | 39,9 ms | 40,9 ms | `Parallel Seq Scan`: o índice não serve |
| Q5 *keyset* (a mesma página 9000: `AND name > 'último'`) | 16,2 ms | **0,111 ms** | `Sort` → `Index Scan` |
Como ler:
- **Q1: 450×.** Sem índice o Postgres lê 180 mil linhas e ordena só para devolver 20; com o índice lê 20. É por isso que o `Index Scan` aparece no plano como `Index Searches: 1` e `Limit` para cedo.
- **Q2: o índice não ajudou.** Com `OFFSET 179980`, o planejador **escolheu** ordenar tudo (mais barato que andar 180 mil entradas do índice mais as buscas na tabela). Deu **408 ms**: é o preço do `OFFSET`.
- **Q5: a mesma página, 3 mil vezes mais barata**, porque `name > 'último'` salta para o ponto certo do índice. Esse é o argumento do cursor.
- **Q3 e Q4: o índice B-tree não resolve.** Para a **busca** com curinga no começo, existe a solução de PostgreSQL: o índice **GIN de trigramas** (`pg_trgm`). Testei **fora do projeto**:
```sql
CREATE EXTENSION pg_trgm;
CREATE INDEX product_name_trgm ON catalog_product USING gin (UPPER(name) gin_trgm_ops);
CREATE INDEX product_sku_trgm  ON catalog_product USING gin (UPPER(sku)  gin_trgm_ops);
-- Q4: 39,9 ms  →  0,258 ms   (Bitmap Heap Scan / BitmapOr nos dois índices)
```
**Não adotei no projeto** porque é recurso **só do PostgreSQL** (o SQLite do desenvolvimento e dos testes não tem `pg_trgm`); adotá-lo exigiria uma migração condicionada ao banco. É uma decisão consciente: aqui a busca é protegida pelo cache (aula 03, 14× mais rápido) e o trigrama fica como o próximo passo se a busca virar gargalo.

**3. O índice adotado no projeto** (`apps/catalog/models.py` + migração `0003_product_active_name_idx`):
```python
class Meta:
    ordering = ["name"]
    constraints = [models.CheckConstraint(condition=Q(price__gte=0), name="product_price_gte_0")]
    indexes = [
        # a listagem pública é `WHERE is_active ORDER BY name LIMIT 20`: este índice a atende sem ordenar
        models.Index(fields=["is_active", "name"], name="product_active_name_idx"),
    ]
```
`makemigrations` gerou `+ Create index product_active_name_idx on field(s) is_active, name of model product`, que funciona nos dois bancos (`Index` genérico). Na API real, com cache desligado, a lista de página 1 levou **26,4 ms** de ponta a ponta (a consulta é 0,04 ms: o resto é o framework e o `COUNT(*)` de 11 ms, que o índice não ajuda). O ganho de **450×** da Q1 só aparece no banco; o do usuário final é menor, e **é por isso que se mede de ponta a ponta antes de comemorar**.

**4. Backup: o script** (`scripts/prod/backup.sh`; usa o `pg_dump` local **ou** um contêiner `postgres:18` só com o cliente, para que a instância EC2 do curso, sem cliente instalado, também rode):
```bash
pgcli pg_dump -Fc --no-owner --no-privileges "${URL%%\?*}" -f "$BACKUP_DIR/$NOME.partial"   # grava num arquivo PARCIAL…
pgcli pg_restore --list "$BACKUP_DIR/$NOME.partial" >/dev/null                                # …confirma que o formato é legível…
mv "$BACKUP_DIR/$NOME.partial" "$BACKUP_DIR/$NOME"                                            # …e só então o nome definitivo
( cd "$BACKUP_DIR" && sha256sum "$NOME" > "$NOME.sha256" )                                    # checksum para detectar adulteração/truncamento
# retenção: mantém os N mais recentes (os nomes têm data UTC: ordem alfabética = cronológica)
```
Execução (PostgreSQL 18.6, 200 064 produtos, retenção 3; 4 execuções):
```text
{"event":"backup_ok","file":"minishop-20261109T022937Z.dump","bytes":11955422,"seconds":1,"kept":1,"s3":"no"}
{"event":"backup_ok","file":"minishop-20261109T022939Z.dump","bytes":11955422,"seconds":1,"kept":2,"s3":"no"}
{"event":"backup_ok","file":"minishop-20261109T022941Z.dump","bytes":11955422,"seconds":1,"kept":3,"s3":"no"}
{"event":"backup_ok","file":"minishop-20261109T022943Z.dump","bytes":11955422,"seconds":1,"kept":3,"s3":"no"}     ← manteve só os 3 mais recentes
```
A tabela de 152 MB em disco virou um arquivo de **11,9 MB** (formato comprimido). A saída é **uma linha JSON** (consistente com os logs da aula 01: um agendador ou o CloudWatch a leem). Defeitos que apareceram ao escrever o script, todos reais: (1) o `mv` rodava no diretório errado porque o contêiner gravava em `BACKUP_DIR` e o `mv` não usava o caminho (o script abortava com `mv: cannot stat ...partial`); (2) os arquivos saíam **do root** porque o contêiner rodava como root (`docker run -u "$(id -u):$(id -g)"`); (3) o contêiner com `-i` **devorava** o resto do arquivo que um `while read` estava lendo (só a primeira tabela era conferida): `</dev/null` na chamada dentro do laço.

**5. O teste de restauração** (`scripts/prod/restore_test.sh`): integridade (SHA-256) → formato legível → restaura num banco temporário → compara as contagens → apaga o temporário:
```text
1/5 integridade do arquivo (SHA-256)           minishop-20261109T023009Z.dump: OK
2/5 formato legível (pg_restore --list)
3/5 restaurar em restore_test_023027
4/5 conferir contagens (restaurado × faixa registrada no backup)
   catalog_product        backup=[200064..200064] restaurado=200064   ok
   catalog_category       backup=[3..3] restaurado=3        ok
   accounts_user          backup=[3..3] restaurado=3        ok
   orders_order           backup=[0..0] restaurado=0        ok
   orders_orderitem       backup=[0..0] restaurado=0        ok
5/5 limpeza
{"event":"restore_test","file":"minishop-20261109T023009Z.dump","restore_seconds":2.2,"ok":true}
```
**Restaurar 200 mil produtos levou ~2 s** (com o servidor de teste, local e sem rede): é o **RTO medido desta máquina**, não o do seu ambiente (num RDS, com rede e disco de verdade, será de minutos). **Registre o seu.** Uma decisão de projeto que um erro meu originou: a primeira versão comparava a contagem restaurada com o banco **ao vivo**, e inserir **um produto depois do backup** a fazia reprovar (falso alarme: o banco continua mudando). Agora o `backup.sh` grava um arquivo `.counts` com as contagens **antes e depois** do dump, e o teste exige que o restaurado caia **dentro dessa faixa** (o instantâneo do `pg_dump` está entre as duas contagens).

**6. O teste do teste: quatro formas de o backup estar ruim.**
```text
1) arquivo TRUNCADO (metade dos bytes):  minishop-...dump: FAILED / sha256sum: WARNING: 1 computed checksum did NOT match
                                          FALHOU: checksum não confere: o arquivo foi alterado ou truncado         (exit 1)
2) UM byte alterado no meio:              o mesmo FAILED do checksum                                               (exit 1)
3) checksum "consertado" à mão (refazendo o .sha256 do arquivo adulterado):
                                          pg_restore: error: could not uncompress data: incorrect data check
                                          FALHOU: pg_restore falhou                                                (exit 1)
4) depois de cada falha:                  select count(*) from pg_database where datname like 'restore_test_%'  →  0
```
Três camadas, três defesas: o **checksum** pega truncamento e adulteração; se alguém "conserta" o checksum, o **próprio formato comprimido** do `pg_restore` pega (verificação de dados); e **o banco temporário é sempre apagado**, até em falha (0 sobraram). Em todos os casos o script **sai com 1**, o que permite ligá-lo a um agendador e a um alerta.

**7. Agendar (não executado).** No servidor (Linux), diariamente às 03:10 UTC o backup e, aos domingos, o teste de restauração; ambos com `flock` para não sobrepor execuções:
```cron
10 3 * * *  flock -n /tmp/minishop-backup.lock bash /opt/minishop/scripts/prod/backup.sh "$DATABASE_URL" /var/backups/minishop 7 >> /var/log/minishop-backup.log 2>&1
40 3 * * 0  flock -n /tmp/minishop-restore.lock bash /opt/minishop/scripts/prod/restore_test.sh "$DATABASE_URL" /var/backups/minishop >> /var/log/minishop-restore.log 2>&1
```
Com `BACKUP_S3_URI=s3://seu-bucket-de-backups/minishop` o `backup.sh` também envia o arquivo e o `.sha256` com criptografia no destino (`--sse AES256`); o papel IAM precisa de `s3:PutObject` **só nesse prefixo** (aula 13.03). **O alerta que importa** não é "o backup rodou", e sim **"não houve backup bem-sucedido nas últimas 26 horas"** (um *heartbeat*: sem notícia, é problema).

**8. O que o RDS já faz e o que você ainda faz.** O RDS mantém **backups automáticos** (retenção que você define) com recuperação para um **ponto no tempo** e *snapshots* manuais; restaurar **cria uma instância nova** (novo endpoint, aula 13.05). O dump lógico continua útil para portabilidade, trocar de versão *major* e para ter uma cópia **fora** da conta/região. O **plano de desastre** completo cabe numa página em `docs/producao.md`: o que fazer, quem faz, em que ordem, o RPO/RTO esperados, e a última vez que **testamos**.

## 🧠 Pausa para lógica
**Problema.** (a) Uma consulta de 5 ms é executada 200 vezes por segundo; outra, de 2 s, roda 3 vezes por dia. Qual vale otimizar primeiro, e que número prova? (b) A tabela `orders` tem um índice em `(user_id, created_at)`. Quais destas consultas o aproveitam? (i) `WHERE user_id=7 ORDER BY created_at DESC LIMIT 10`; (ii) `WHERE created_at > '2026-01-01'`; (iii) `WHERE user_id=7`. (c) Backups diários às 03:00, banco perde-se às 16:00 do mesmo dia: qual a perda de dados (RPO efetivo)? O que o PITR do RDS muda? (d) O restore leva 40 min. A diretoria exige RTO de 15 min. Cite duas ações.

<details><summary>Dica</summary>Tempo total = frequência × duração. O índice composto serve a prefixos da esquerda para a direita.</details>

<details><summary>Solução comentada</summary>

(a) A de 5 ms: 5 ms × 200 × 86 400 ≈ **86 400 s/dia (~24 h de CPU de banco)**, contra 2 s × 3 = **6 s/dia**. O `pg_stat_statements` ordenado por `total_exec_time` mostra isso. (b) (i) **sim** (usa `user_id` para filtrar e `created_at` para ordenar); (iii) **sim** (prefixo `user_id`); (ii) **não** bem: o filtro só por `created_at` não é prefixo; precisaria de um índice com `created_at` primeiro. (c) Até **13 h de dados** perdidos (de 03:00 às 16:00). Com **PITR**, recupera-se para um instante qualquer (o RPO cai para minutos, limitado ao arquivamento de WAL). (d) Reduzir o volume a restaurar (arquivar/particionar dados antigos), restaurar de um **snapshot** na mesma região (mais rápido que dump lógico), ter uma **réplica/Multi-AZ** pronta para assumir, ou automatizar e ensaiar o procedimento para eliminar o tempo de decisão. A meta só se confirma **medindo** o restore.
</details>

## ⚠️ Erros comuns e boas práticas
| Sintoma / mensagem | Causa | Solução |
|---|---|---|
| "Adicionei cache e continua lento" | Não sabe qual consulta é a culpada | Log de lentas + `pg_stat_statements` por tempo **total** |
| `EXPLAIN ANALYZE` apagou/alterou dados | Executa o comando de verdade | Em `BEGIN; ...; ROLLBACK;` |
| Índice criado e nada mudou | Ordem das colunas errada, ou o planejador prefere `Seq Scan` (tabela pequena/estatística velha) | `ANALYZE`; conferir o plano; ordem das colunas |
| `COUNT(*)` lento | Precisa contar; índice não ajuda | Cache da contagem, contagem aproximada, ou cursor sem total |
| Páginas fundas lentas | `OFFSET` grande | `CursorPagination`/keyset |
| Busca `%texto%` lenta | Curinga no começo | `pg_trgm` + GIN (PostgreSQL), ou busca textual |
| Escritas ficaram lentas | Índices demais | Remover os não usados (`pg_stat_user_indexes`) |
| Backup "ok" mas não restaura | Nunca testado; arquivo parcial; checksum ausente | `restore_test.sh` periódico; arquivo `.partial`; SHA-256 |
| `pg_restore: error: role "x" does not exist` | Dono dos objetos inexistente | `--no-owner` (e `--no-privileges`) |
| Backup cresce até encher o disco | Sem retenção | Manter N; enviar a armazenamento externo |
| `mv: cannot stat ...partial` no script | Diretório de trabalho ≠ pasta do contêiner | Caminhos absolutos |
| Arquivos de backup "do root" | Contêiner rodando como root | `docker run -u "$(id -u):$(id -g)"` |
| Teste de restauração com falso alarme | Comparou com o banco **ao vivo** | Faixa registrada no momento do backup |
| Backup com dados pessoais num bucket aberto | Falta de proteção | Bucket privado, cifrado, retenção definida (LGPD) |
- **Meça, mude uma coisa, meça de novo.** E registre antes/depois.
- **Índice é um custo contínuo:** crie para consultas frequentes e **revise** o que não é usado.
- **Backup = RPO + RTO + teste + local externo.** Se uma dessas faltar, é uma suposição.
- **Dados de produção em ambiente de teste exigem anonimização** (aula 9.07).

## 🧩 Exercícios
**1. Fixação.** (a) Por que ordenar `pg_stat_statements` pelo tempo **total**? (b) O que o `Seq Scan` indica e quando é aceitável? (c) Por que `OFFSET` fundo é caro e o cursor não? (d) RPO × RTO. (e) Por que testar a restauração?

<details><summary>Solução</summary>

(a) Pelo impacto agregado: frequência × duração. (b) Leitura de toda a tabela; aceitável em tabelas pequenas ou quando a consulta retorna grande parte das linhas. (c) `OFFSET` produz e descarta N linhas; o cursor usa o índice para saltar. (d) RPO: quanto dado se aceita perder; RTO: em quanto tempo se volta. (e) Porque só a restauração prova que o backup serve, e mede o RTO.
</details>

**2. Aplicação no projeto MiniShop (fecha o marco `v4.1-producao`).**
- [ ] Um PostgreSQL de teste com `pg_stat_statements` e `log_min_duration_statement`, **200 mil produtos**, e a **tabela de `pg_stat_statements` por tempo total** do seu tráfego simulado, com a análise "qual é o maior custo agregado"
- [ ] A tabela **sem/com índice** das consultas Q1 a Q5 (seus números), o índice `product_active_name_idx` no modelo e a migração; suíte verde em SQLite **e** PostgreSQL
- [ ] O experimento do **trigrama** fora do projeto, com a decisão (adotar ou não) justificada por escrito
- [ ] `scripts/prod/backup.sh` e `restore_test.sh` rodando contra o seu PostgreSQL de teste, com a saída JSON de cada um e o **RTO medido**
- [ ] Os **quatro cenários de falha** (truncado, byte alterado, checksum "consertado", e a prova de que o banco temporário some)
- [ ] `docs/producao.md` com **RPO/RTO** declarados, o procedimento de restauração em passos e a data do último teste; o agendamento (`cron`/timer) e o alerta de "sem backup em 26 h"
- [ ] Marco completo: `/health/` e `/health/ready/`, logs JSON com `request_id`, Sentry configurado (aula 02), cache no catálogo (aula 03), backup e restauração testados; **suíte, `ruff`, `mypy`, `lint-imports`, `makemigrations --check` e OpenAPI limpos**
- [ ] `git tag -a v4.1-producao -m "MiniShop: produção e observabilidade" && git push --follow-tags`
- [ ] Commit `feat(ops): slow query analysis, product index and backup/restore scripts`

**3. Desafio (opcional).** Troque a paginação por páginas do catálogo por `CursorPagination` ordenada por `(name, id)` e meça a página "9000" (do ponto de vista do cliente) antes e depois. Liste o que **muda no contrato da API** (o cliente deixa de poder pedir `?page=N`) e o que isso exige do front-end.

## 🎤 Na entrevista
**1. Como você acha e corrige uma consulta lenta?** Começo pelas métricas por rota para achar o endpoint, depois olho no banco: log de consultas lentas e `pg_stat_statements` ordenado por tempo total. Examino o plano com `EXPLAIN (ANALYZE, BUFFERS)`, corrijo (índice, reescrita, paginação) e comparo antes e depois; só então considero cache.

**2. Quando um índice não ajuda?** Para `COUNT(*)`, para `LIKE '%x%'` com curinga no início (precisa de trigramas), quando a coluna filtrada não é o prefixo do índice composto, em tabelas pequenas, e quando a consulta devolve grande parte da tabela; e ele custa em escritas e espaço.

**3. Como você garante que seus backups funcionam?** Backups automáticos e verificados (checksum, leitura do formato), guardados fora do servidor e cifrados, com retenção; um teste periódico de restauração num ambiente temporário que confere o conteúdo e mede o tempo (RTO), com alerta se não houver backup recente; e RPO/RTO definidos com o negócio.

## 📚 Para ir além
- 📄 Documentação oficial: [PostgreSQL — usando o `EXPLAIN`](https://www.postgresql.org/docs/18/using-explain.html) e [tipos de índice](https://www.postgresql.org/docs/18/indexes.html). Ler planos e escolher índices.
- 📄 Documentação oficial: [`pg_stat_statements`](https://www.postgresql.org/docs/18/pgstatstatements.html), [parâmetros de log (`log_min_duration_statement`)](https://www.postgresql.org/docs/18/runtime-config-logging.html) e [`pg_trgm`](https://www.postgresql.org/docs/18/pgtrgm.html).
- 📄 Documentação oficial: [Django — índices](https://docs.djangoproject.com/en/5.2/ref/models/indexes/) e [otimização de acesso ao banco](https://docs.djangoproject.com/en/5.2/topics/db/optimization/).
- 📄 Documentação oficial: [DRF — paginação](https://www.django-rest-framework.org/api-guide/pagination/) (`CursorPagination`) e o artigo [Use The Index, Luke — paginação sem OFFSET](https://use-the-index-luke.com/no-offset) (em inglês).
- 📄 Documentação oficial: [PostgreSQL — backup lógico (`pg_dump`)](https://www.postgresql.org/docs/18/backup-dump.html), [`pg_restore`](https://www.postgresql.org/docs/18/app-pgrestore.html) e [arquivamento contínuo/PITR](https://www.postgresql.org/docs/18/continuous-archiving.html).
- 📄 Documentação oficial: [RDS — backups automáticos](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_WorkingWithAutomatedBackups.html). Retenção, PITR e restauração para nova instância.
- 🏋️ Prática extra: crie o índice `(is_active, name)` e **ligue o `EXPLAIN`** da consulta do staff (`ORDER BY name` sem filtro): ele usa o índice? Por quê? Que índice o atenderia?

## ✅ Checklist da aula
- [ ] Sei achar consultas lentas por log de lentas e `pg_stat_statements` (por tempo total)
- [ ] Sei ler um plano e provar o ganho do índice, e sei onde o índice **não** ajuda
- [ ] Entendo `OFFSET` × cursor e tenho números dos dois
- [ ] O índice do catálogo está no modelo, com migração, e a suíte passa nos dois bancos
- [ ] Faço backup consistente, verificado e com retenção; testo a restauração e conheço o RTO medido
- [ ] Sei RPO, RTO, a regra 3-2-1 e o que o RDS faz por mim
