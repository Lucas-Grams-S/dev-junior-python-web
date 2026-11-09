# 09. Transações, ACID e níveis de isolamento

> ⏱️ ~1h30 · Módulo 3 · Pré-requisitos: [03](03-postgres-docker-ddl-dml.md), [08](08-constraints-indices-explain.md); *context managers* da [aula 1.16](../01-python-logica/16-decorators-context-managers.md)

## 🎯 Objetivos
Ao final desta aula você consegue:
- Explicar o que é uma transação e usar `BEGIN`, `COMMIT`, `ROLLBACK` e `SAVEPOINT`
- Explicar as propriedades ACID com o exemplo da transferência entre contas
- Descrever os níveis de isolamento do PostgreSQL e as anomalias que cada um evita
- Evitar *lost update* com atualização atômica ou `SELECT ... FOR UPDATE`
- Reconhecer um *deadlock* e como preveni-lo

## 🤔 Por que isso importa
Criar um pedido no MiniShop é **várias** operações: gravar o pedido, gravar os itens, baixar o estoque e registrar o pagamento. Se a energia cair no meio, ou duas pessoas comprarem o último item ao mesmo tempo, o sistema não pode ficar com dinheiro cobrado sem pedido, nem com estoque negativo. Transações são a ferramenta que dá essa garantia, e `transaction.atomic()` do Django (Módulo 5) é apenas um *wrapper* delas.

## 💡 Intuição (explicação simples)
Transferir R$ 100 da conta A para a conta B são duas etapas: **tirar de A** e **colocar em B**. Se o sistema cai entre as duas, o dinheiro some. Uma transação é **um envelope lacrado**: tudo o que você faz dentro dele só “vale” quando você o fecha com `COMMIT`; se algo der errado, você o rasga (`ROLLBACK`) e **nada** aconteceu. E, enquanto o envelope está aberto, quem está de fora não vê o rascunho pela metade.

## 🔬 Como funciona por dentro
**ACID**

| Letra | Garantia | Como o PostgreSQL entrega |
|---|---|---|
| **A**tomicidade | tudo ou nada | `ROLLBACK` descarta todas as mudanças da transação |
| **C**onsistência | de um estado válido a outro válido (constraints sempre respeitadas) | `CHECK`, `FK`, `UNIQUE` validados; se violar, a transação falha |
| **I**solamento | transações concorrentes não se enxergam pela metade | MVCC (versões de linhas) + travas |
| **D**urabilidade | depois do `COMMIT`, o dado sobrevive a quedas | WAL (*write-ahead log*) gravado em disco antes de confirmar |

- Por padrão cada comando sozinho é uma transação (*autocommit*). `BEGIN` abre uma transação explícita com vários comandos.
- Se um comando falha **dentro** de uma transação, ela entra em estado abortado: tudo o que vier depois é ignorado até o `ROLLBACK`.
- **MVCC** (*multi-version concurrency control*): ao alterar uma linha, o PostgreSQL cria uma **nova versão**; quem está lendo continua vendo a versão antiga que correspondia ao seu *snapshot*. Por isso **leitores não bloqueiam escritores** (e vice-versa). Escritores da *mesma linha* esperam um pelo outro (trava de linha).

**Níveis de isolamento** (o padrão do PostgreSQL é `READ COMMITTED`):

| Nível | Cada comando vê… | Evita |
|---|---|---|
| `READ COMMITTED` (padrão) | o que estava confirmado **quando o comando começou** | leitura suja |
| `REPEATABLE READ` | o mesmo *snapshot* durante toda a transação | + leitura não repetível e fantasmas |
| `SERIALIZABLE` | como se as transações rodassem uma por vez (pode abortar com erro de serialização; é preciso repetir) | + anomalias como *write skew* |

(O PostgreSQL não tem “leitura suja” (`READ UNCOMMITTED` se comporta como `READ COMMITTED`).)

**Anomalias:** *leitura não repetível* (lê duas vezes a mesma linha e o valor mudou); *fantasma* (a mesma consulta devolve linhas novas); *lost update* (duas transações leem, calculam e gravam, e uma sobrescreve a outra); *write skew* (duas transações leem o mesmo conjunto e atualizam linhas diferentes, violando uma regra global). **Deadlock:** A espera B e B espera A; o PostgreSQL detecta e aborta uma delas.

## 🛠️ Exemplo prático
Banco `loja` (aula 03). Todos os blocos foram executados; as saídas são reais.

**1. Atomicidade: a transferência**
```sql
CREATE TABLE accounts (
    id      integer PRIMARY KEY,
    owner   text    NOT NULL,
    balance numeric(12,2) NOT NULL CHECK (balance >= 0)
);
INSERT INTO accounts VALUES (1, 'Ana', 500.00), (2, 'Bruno', 100.00);

BEGIN;
UPDATE accounts SET balance = balance - 200 WHERE id = 1;
UPDATE accounts SET balance = balance + 200 WHERE id = 2;
COMMIT;
SELECT * FROM accounts ORDER BY id;
```
```text
 id | owner | balance 
----+-------+---------
  1 | Ana   |  300.00
  2 | Bruno |  300.00
(2 rows)
```
**2. Falha no meio: nada fica pela metade**
```sql
BEGIN;
UPDATE accounts SET balance = balance + 500 WHERE id = 2;     -- 1ª etapa funciona
UPDATE accounts SET balance = balance - 500 WHERE id = 1;     -- 2ª etapa viola o CHECK (saldo ficaria -200)
SELECT 'não chego aqui' AS msg;                               -- ignorado: transação abortada
ROLLBACK;
SELECT * FROM accounts ORDER BY id;                            -- tudo como antes
```
```text
 id | owner | balance 
----+-------+---------
  1 | Ana   |  300.00
  2 | Bruno |  300.00
(2 rows)

ERROR:  new row for relation "accounts" violates check constraint "accounts_balance_check"
DETAIL:  Failing row contains (1, Ana, -200.00).
ERROR:  current transaction is aborted, commands ignored until end of transaction block
```
O `CHECK (balance >= 0)` é a **consistência**: o banco recusa o estado inválido, e a atomicidade desfaz também a primeira etapa. Sem transação, Bruno teria ficado com os R$ 500 a mais.

**3. `SAVEPOINT`: desfazer só uma parte**
```sql
BEGIN;
UPDATE accounts SET balance = balance + 10 WHERE id = 1;
SAVEPOINT depois_do_bonus;
UPDATE accounts SET balance = balance - 99999 WHERE id = 1;   -- vai falhar
ROLLBACK TO depois_do_bonus;                                   -- volta só até o savepoint
UPDATE accounts SET balance = balance + 5 WHERE id = 2;
COMMIT;
SELECT * FROM accounts ORDER BY id;
```
```text
 id | owner | balance 
----+-------+---------
  1 | Ana   |  310.00
  2 | Bruno |  305.00
(2 rows)

ERROR:  new row for relation "accounts" violates check constraint "accounts_balance_check"
DETAIL:  Failing row contains (1, Ana, -99689.00).
```
**4. O pedido do MiniShop: tudo ou nada**
```sql
BEGIN;
INSERT INTO orders (user_id, status, total) VALUES (5, 'pending', 0) RETURNING id AS novo_pedido \gset
-- item 1: estoque suficiente (atualização condicional e atômica)
UPDATE products SET stock = stock - 2 WHERE id = 1 AND stock >= 2;
INSERT INTO order_items (order_id, product_id, quantity, unit_price) SELECT :novo_pedido, id, 2, price FROM products WHERE id = 1;
-- item 2: produto 5 está sem estoque: a restrição CHECK (stock >= 0) derruba a transação
UPDATE products SET stock = stock - 1 WHERE id = 5;
ROLLBACK;

SELECT count(*) AS pedidos_da_elisa FROM orders WHERE user_id = 5;    -- 0: nenhum rastro do pedido
SELECT id, stock FROM products WHERE id IN (1, 5) ORDER BY id;          -- estoque intacto
```
```text
 pedidos_da_elisa 
------------------
                0
(1 row)

 id | stock 
----+-------
  1 |     4
  5 |     0
(2 rows)

ERROR:  new row for relation "products" violates check constraint "products_stock_check"
DETAIL:  Failing row contains (5, 1, PF-05, webcam-full-hd, Webcam Full HD, , 219.90, -1, t, 2026-01-09 10:00:00+00).
```
No Django isso será `with transaction.atomic(): ...` e uma exceção dentro do bloco faz o *rollback* de tudo (Módulo 5, aula 17).

**5. Isolamento: leitura não repetível (duas sessões ao mesmo tempo)**

Abrimos **duas conexões** no mesmo banco. A sessão A lê o estoque duas vezes, 1,5 s de intervalo; a sessão B altera o estoque no meio.
```bash
run() { docker exec -i minishop-pg psql -U postgres -d loja -X -q -P pager=off; }
for nivel in "READ COMMITTED" "REPEATABLE READ"; do
  echo "=== nível: $nivel"
  echo "UPDATE products SET stock = 4 WHERE id = 1;" | run
  ( run <<SQL
BEGIN ISOLATION LEVEL $nivel;
SELECT 'A, 1ª leitura' AS quando, stock FROM products WHERE id = 1;
\o /dev/null
SELECT pg_sleep(1.5);
\o
SELECT 'A, 2ª leitura' AS quando, stock FROM products WHERE id = 1;
COMMIT;
SQL
  ) > a.txt 2>&1 &
  sleep 0.6
  run <<'SQL'
UPDATE products SET stock = stock + 100 WHERE id = 1;
SQL
  wait; cat a.txt
done
```
```text
=== nível: READ COMMITTED
    quando     | stock 
---------------+-------
 A, 1ª leitura |     4
(1 row)

    quando     | stock 
---------------+-------
 A, 2ª leitura |   104
(1 row)

=== nível: REPEATABLE READ
    quando     | stock 
---------------+-------
 A, 1ª leitura |     4
(1 row)

    quando     | stock 
---------------+-------
 A, 2ª leitura |     4
(1 row)
```
Em `READ COMMITTED` a 2ª leitura **vê** a alteração de B (cada comando tem seu próprio *snapshot*). Em `REPEATABLE READ` a transação continua vendo o estoque original. Escolha conforme a necessidade: relatórios que somam várias consultas precisam de `REPEATABLE READ` para ficarem coerentes.

**6. *Lost update*: ler, calcular e gravar**
```bash
run() { docker exec -i minishop-pg psql -U postgres -d loja -X -q -t -A -P pager=off; }
run <<'SQL'
UPDATE products SET stock = 10 WHERE id = 2;
SQL
echo "--- ERRADO: lê, calcula no cliente, grava (2 vendedores: -3 e -4)"
( run <<'SQL'
BEGIN;
SELECT 'A leu ' || stock FROM products WHERE id = 2;
\o /dev/null
SELECT pg_sleep(1);
\o
UPDATE products SET stock = 10 - 3 WHERE id = 2;
COMMIT;
SQL
) > a.txt 2>&1 &
sleep 0.4
run <<'SQL'
BEGIN;
SELECT 'B leu ' || stock FROM products WHERE id = 2;
UPDATE products SET stock = 10 - 4 WHERE id = 2;
COMMIT;
SQL
wait; cat a.txt
echo "estoque final: $(run <<<'SELECT stock FROM products WHERE id = 2;')  (vendeu 3 + 4, mas só descontou um)"
echo "--- CERTO 1: atualização atômica no banco"
run <<'SQL'
UPDATE products SET stock = 10 WHERE id = 2;
UPDATE products SET stock = stock - 3 WHERE id = 2 AND stock >= 3;
UPDATE products SET stock = stock - 4 WHERE id = 2 AND stock >= 4;
SELECT 'estoque final: ' || stock FROM products WHERE id = 2;
SQL
```
```text
--- ERRADO: lê, calcula no cliente, grava (2 vendedores: -3 e -4)
B leu 10
A leu 10
estoque final: 7  (vendeu 3 + 4, mas só descontou um)
--- CERTO 1: atualização atômica no banco
estoque final: 3
```
**7. `SELECT ... FOR UPDATE`: travar a linha enquanto decide**
```bash
run() { docker exec -i minishop-pg psql -U postgres -d loja -X -q -t -A -P pager=off; }
run <<'SQL'
UPDATE products SET stock = 10 WHERE id = 2;
SQL
( run <<'SQL'
BEGIN;
SELECT 'A travou a linha, estoque=' || stock FROM products WHERE id = 2 FOR UPDATE;
\o /dev/null
SELECT pg_sleep(1.5);
\o
UPDATE products SET stock = stock - 3 WHERE id = 2;
COMMIT;
SELECT 'A confirmou';
SQL
) > a.txt 2>&1 &
sleep 0.5
run <<'SQL'
BEGIN;
SELECT 'B tentando travar...';
SELECT 'B obteve a trava e viu estoque=' || stock FROM products WHERE id = 2 FOR UPDATE;
UPDATE products SET stock = stock - 4 WHERE id = 2;
COMMIT;
SELECT 'B confirmou';
SQL
wait; cat a.txt
echo "estoque final: $(run <<<'SELECT stock FROM products WHERE id = 2;')"
```
```text
B tentando travar...
B obteve a trava e viu estoque=7
B confirmou
A travou a linha, estoque=10
A confirmou
estoque final: 3
```
B **esperou** A confirmar e só então leu o valor já atualizado (7), chegando a 3 no final. Use `FOR UPDATE` quando a decisão depende do valor lido (por exemplo, calcular desconto pelo saldo); para um simples decremento, o `UPDATE ... WHERE stock >= n` basta. No Django: `select_for_update()`.

**8. Deadlock**
```bash
run() { docker exec -i minishop-pg psql -U postgres -d loja -X -q -t -A -P pager=off; }
( run <<'SQL'
BEGIN;
UPDATE accounts SET balance = balance WHERE id = 1;
\o /dev/null
SELECT pg_sleep(1);
\o
UPDATE accounts SET balance = balance WHERE id = 2;
COMMIT;
SELECT 'A terminou';
SQL
) > a.txt 2>&1 &
sleep 0.3
run <<'SQL' > b.txt 2>&1
BEGIN;
UPDATE accounts SET balance = balance WHERE id = 2;
\o /dev/null
SELECT pg_sleep(1);
\o
UPDATE accounts SET balance = balance WHERE id = 1;
COMMIT;
SELECT 'B terminou';
SQL
wait; echo "--- sessão A:"; cat a.txt; echo "--- sessão B:"; cat b.txt
```
```text
--- sessão A:
ERROR:  deadlock detected
DETAIL:  Process 2143 waits for ShareLock on transaction 1387; blocked by process 2150.
Process 2150 waits for ShareLock on transaction 1386; blocked by process 2143.
HINT:  See server log for query details.
CONTEXT:  while updating tuple (0,7) in relation "accounts"
A terminou
--- sessão B:
B terminou
```
A travou a conta 1 e quer a 2; B travou a 2 e quer a 1: ninguém avança. (O `SELECT 'A terminou'` aparece mesmo assim porque o script do `psql` não para no erro; o `COMMIT` de uma transação abortada vira `ROLLBACK`. Qual sessão é a “vítima” varia de execução para execução.) O PostgreSQL detecta o ciclo (após `deadlock_timeout`, 1 s por padrão) e **aborta uma das transações** com `ERROR: deadlock detected`; a outra termina. **Prevenção:** adquira travas **sempre na mesma ordem** (por exemplo, ordenando os IDs antes de atualizar) e mantenha transações curtas.

## ⚠️ Erros comuns e boas práticas
| Mensagem / sintoma | Causa | Solução |
|---|---|---|
| `ERROR: current transaction is aborted, commands ignored until end of transaction block` | Houve um erro e você continuou na mesma transação | `ROLLBACK` (ou `ROLLBACK TO savepoint`) |
| `ERROR: deadlock detected` | Duas transações travam linhas em ordem oposta | Ordem fixa de travas; transações curtas; **repetir** a transação |
| `ERROR: could not serialize access due to concurrent update` | Conflito em `REPEATABLE READ`/`SERIALIZABLE` | **Repetir a transação inteira** |
| Sessão “trava” sem erro | Esperando a trava de outra transação aberta | Veja `pg_stat_activity`; feche a transação esquecida |
| Estoque negativo / venda duplicada | *Lost update* (ler-calcular-gravar) | `UPDATE ... SET x = x - n WHERE x >= n` ou `FOR UPDATE` |
| `idle in transaction` por horas | Aplicação abriu `BEGIN` e não fechou | Sempre `COMMIT`/`ROLLBACK`; use `with` |

- **Mantenha transações curtas**: nada de chamar API externa, enviar e-mail ou esperar o usuário *dentro* de uma transação.
- **Decida e valide no banco** (`WHERE stock >= n`, `CHECK`): a aplicação concorrente não é confiável sozinha.
- Em `SERIALIZABLE`/`REPEATABLE READ` e em deadlocks, o erro é **esperado**: a aplicação deve repetir a transação.
- `COMMIT` confirma; o que não foi confirmado some se a conexão cair. Nunca presuma gravação sem `COMMIT`.

## 🧠 Pausa para lógica
**Problema (transação em Python).** Escreva um *context manager* `transacao(dados)` que, se o bloco `with` levantar exceção, **restaura** o dicionário ao estado anterior (rollback); use-o numa transferência com saldo insuficiente.

<details><summary>Dica</summary>
Em <code>__enter__</code>, guarde <code>copy.deepcopy(dados)</code>; em <code>__exit__</code>, se <code>tipo</code> não for <code>None</code>, restaure com <code>dados.clear(); dados.update(copia)</code> e devolva <code>False</code> para a exceção continuar subindo.
</details>

<details><summary>Solução comentada</summary>

```python
import copy
from contextlib import contextmanager

@contextmanager
def transacao(dados):
    snapshot = copy.deepcopy(dados)            # BEGIN
    try:
        yield dados
    except BaseException:
        dados.clear(); dados.update(snapshot)  # ROLLBACK
        raise
    # sem exceção: COMMIT (nada a fazer)

contas = {"ana": 500, "bruno": 100}

def transferir(origem, destino, valor):
    with transacao(contas):
        contas[destino] += valor
        if contas[origem] < valor:
            raise ValueError("saldo insuficiente")
        contas[origem] -= valor

transferir("ana", "bruno", 200)
print(contas)
try:
    transferir("bruno", "ana", 9999)
except ValueError as e:
    print("falhou:", e, "|", contas)           # destino NÃO ficou com o valor a mais
```
```text
{'ana': 300, 'bruno': 300}
falhou: saldo insuficiente | {'ana': 300, 'bruno': 300}
```
Sem o `with transacao`, `contas["ana"]` teria recebido 9.999 antes de a validação falhar. É exatamente o papel do `ROLLBACK`. (Em Python isso só funciona em um processo; entre processos e máquinas, só o banco pode garantir.)
</details>

**Variação mais difícil:** como evitar *deadlock* em `transferir(a, b)` e `transferir(b, a)` simultâneas? (Dica: trave primeiro o menor id.)

## 🧩 Exercícios
**1. Fixação**
Que anomalia ocorre em cada caso e qual nível de isolamento a evita? (a) Uma transação lê o saldo duas vezes e obtém valores diferentes. (b) Dois caixas leem saldo 100 e cada um grava 100−30 e 100−50. (c) Duas transações se esperam mutuamente.

<details><summary>Solução</summary>

(a) Leitura não repetível; `REPEATABLE READ` (ou superior). (b) *Lost update*; atualização atômica (`SET saldo = saldo − n`), `FOR UPDATE`, ou `REPEATABLE READ`/`SERIALIZABLE` (que abortam e exigem repetir). (c) *Deadlock*; nenhum nível evita: o banco detecta e aborta uma, e a prevenção é a ordem de travas.
</details>

**2. Aplicação no projeto MiniShop**
Escreva `projeto/sql/transacoes/criar_pedido.sql`: o script que cria um pedido do carrinho do usuário 2, de forma atômica e segura contra concorrência.

Critérios de pronto:
- [ ] Dentro de `BEGIN … COMMIT`: cria o pedido, copia os `cart_items` para `order_items` com o `unit_price` **atual**, baixa o estoque com `UPDATE … WHERE stock >= quantity` e esvazia o carrinho
- [ ] Se algum item não tem estoque suficiente, **nada** é gravado (demonstre com um `ROLLBACK`/erro)
- [ ] O `total` do pedido é calculado a partir dos itens (e a consulta de auditoria da aula 06 continua vazia)
- [ ] Teste de concorrência com duas sessões (como na seção 7) comprando o último item: apenas uma conclui
- [ ] Um parágrafo no `README` explicando por que a decisão “há estoque?” está na cláusula `WHERE` do `UPDATE`
- [ ] Commit `feat(sql): atomic order creation`

<details><summary>Solução de referência</summary>

```sql
BEGIN;
WITH total AS (
    SELECT sum(ci.quantity * p.price) AS t
    FROM carts c JOIN cart_items ci ON ci.cart_id = c.id JOIN products p ON p.id = ci.product_id
    WHERE c.user_id = 2
), novo AS (
    INSERT INTO orders (user_id, status, total) SELECT 2, 'pending', t FROM total RETURNING id
), itens AS (
    INSERT INTO order_items (order_id, product_id, quantity, unit_price)
    SELECT novo.id, ci.product_id, ci.quantity, p.price
    FROM novo, carts c JOIN cart_items ci ON ci.cart_id = c.id JOIN products p ON p.id = ci.product_id
    WHERE c.user_id = 2
    RETURNING product_id, quantity
), baixa AS (
    UPDATE products p SET stock = p.stock - i.quantity FROM itens i
    WHERE p.id = i.product_id AND p.stock >= i.quantity
    RETURNING p.id
), limpa AS (
    DELETE FROM cart_items WHERE cart_id IN (SELECT id FROM carts WHERE user_id = 2) RETURNING 1
)
SELECT (SELECT id FROM novo) AS pedido, (SELECT t FROM total) AS total,
       (SELECT count(*) FROM itens) AS itens_gravados,
       (SELECT count(*) FROM baixa) AS estoques_baixados,
       (SELECT count(*) FROM limpa) AS itens_do_carrinho_removidos;
ROLLBACK;     -- troque por COMMIT em produção
```
```text
 pedido | total  | itens_gravados | estoques_baixados | itens_do_carrinho_removidos 
--------+--------+----------------+-------------------+-----------------------------
     20 | 488.80 |              2 |                 2 |                           2
(1 row)
```
O padrão: se `estoques_baixados` for menor que `itens_gravados`, algum item não tinha estoque: a aplicação faz `ROLLBACK` e avisa o usuário. O Django fará o mesmo com `transaction.atomic()` e uma exceção (Módulo 5).
</details>

**3. Desafio (opcional)**
Reproduza um *write skew*: duas transações em `REPEATABLE READ` verificam “há pelo menos 1 plantonista de sobreaviso?” e cada uma remove um plantonista diferente. Depois repita com `SERIALIZABLE` e observe o erro.

## 🎤 Na entrevista
- **O que é ACID?** Atomicidade (tudo ou nada), Consistência (respeita as regras), Isolamento (transações concorrentes não se interferem) e Durabilidade (confirmado não se perde).
- **Qual o nível de isolamento padrão do PostgreSQL e o que ele permite?** `READ COMMITTED`: cada comando vê os dados confirmados até aquele momento; permite leitura não repetível e fantasmas. Para consistência dentro da transação: `REPEATABLE READ` ou `SERIALIZABLE`.
- **Como evitar vender o mesmo item duas vezes?** Atualização atômica e condicional (`UPDATE ... SET stock = stock - n WHERE stock >= n`, conferindo o nº de linhas afetadas) ou `SELECT ... FOR UPDATE`, sempre dentro de uma transação, mais `CHECK (stock >= 0)` como rede de segurança.
- **O que é um deadlock e como preveni-lo?** Duas transações esperando travas uma da outra; o banco aborta uma. Prevenção: ordem consistente de travas, transações curtas, e retentativa.

## 📚 Para ir além
- 📄 Documentação oficial: [Transações (tutorial)](https://www.postgresql.org/docs/current/tutorial-transactions.html). `BEGIN`, `COMMIT`, `ROLLBACK`, `SAVEPOINT`.
- 📄 Documentação oficial: [Isolamento de transações](https://www.postgresql.org/docs/current/transaction-iso.html). Níveis e anomalias com exemplos.
- 📄 Documentação oficial: [Controle de concorrência (MVCC)](https://www.postgresql.org/docs/current/mvcc.html). Travas de linha e `FOR UPDATE`.
- 🎥 Vídeo (EN): *CS50 SQL* ([cs50.harvard.edu/sql](https://cs50.harvard.edu/sql/)), aula sobre transações e concorrência.
- 🏋️ Prática extra: reproduza a seção 5 com `SERIALIZABLE` e o conflito de duas atualizações; leia o erro.

## ✅ Checklist da aula
- [ ] Fiz transações com `COMMIT`, `ROLLBACK` e `SAVEPOINT`
- [ ] Vi a diferença entre `READ COMMITTED` e `REPEATABLE READ` com duas sessões
- [ ] Reproduzi *lost update*, `FOR UPDATE` e deadlock
- [ ] Entreguei `criar_pedido.sql`
