# 12. Mini-projeto: banco da loja em SQL puro

> ⏱️ ~1h30 · Módulo 3 · Pré-requisitos: aulas [01](01-por-que-banco-modelagem-er.md) a [11](11-orm-migracoes-nosql.md)

## 🎯 Objetivos
Ao final desta aula você consegue:
- Organizar o banco do MiniShop em arquivos SQL versionados e reproduzíveis (schema, seed, índices, views, funções)
- Automatizar a criação do zero com um script e **verificar a integridade** com consultas de auditoria
- Criar views e uma *materialized view* para relatórios, e uma função PL/pgSQL transacional para criar pedidos
- Fazer backup e restauração com `pg_dump`/`pg_restore` e **provar** que a cópia está íntegra
- Descobrir a ordem correta de criação/remoção de tabelas a partir das chaves estrangeiras

## 🤔 Por que isso importa
Este é o banco que o Django (Módulo 5) vai assumir: as mesmas tabelas, o mesmo seed. Um banco que só existe na cabeça de quem o montou, ou que ninguém sabe recriar, é uma bomba-relógio. Saber **reconstruir tudo com um comando**, **verificar que está certo** e **restaurar um backup** é rotina de qualquer time, e é o que se espera de um júnior que “mexe em banco”.

## 💡 Intuição (explicação simples)
É escrever a **planta e o manual da obra**: a planta (schema), a mobília inicial (seed), os atalhos (índices e views) e a **checklist de vistoria** (verify). Com isso qualquer pessoa derruba e reconstrói o prédio idêntico em minutos, e o seguro (backup) permite voltar ao estado de ontem.

## 🔬 Como funciona por dentro
**Estrutura do projeto** (tudo em `projeto/sql/`):
```text
projeto/sql/
├── 01_schema.sql      # tabelas, PKs, FKs, CHECKs (a "planta")
├── 02_seed.sql        # dados de exemplo
├── 03_indices.sql     # índices das aulas 08
├── 04_views.sql       # views e materialized view
├── 05_funcoes.sql     # fn_create_order (aula 09 em PL/pgSQL)
├── verify.sql         # consultas de auditoria: falham com erro se algo estiver errado
├── run_all.sh         # recria o banco do zero e aplica tudo em ordem
├── consultas/         # catalogo.sql, pedidos.sql, relatorios.sql (aulas 04 a 06)
└── exercicios/        # respostas.sql (aula 07)
```
```mermaid
flowchart LR
    S[01 schema] --> D[02 seed] --> I[03 índices] --> V[04 views] --> F[05 funções] --> C{verify.sql}
    C -- ok --> OK[banco pronto]
    C -- falha --> E[erro com a lista de problemas]
```
- **View**: consulta com nome (`SELECT` salvo). Não guarda dados; sempre reflete as tabelas. **Materialized view**: guarda o *resultado* (rápida de ler) e precisa de `REFRESH`. Boas para relatórios pesados que toleram pequeno atraso.
- **Função PL/pgSQL**: lógica dentro do banco. Ela roda **na transação de quem a chamou**: se levantar exceção, tudo o que fez é desfeito.
- **`pg_dump`**: exporta schema e dados (`-Fc` = formato “custom”, compactado, restaurável por `pg_restore`, inclusive de forma parcial e paralela). Um backup só vale depois de **testar a restauração**.
- **Ordem de dependência:** uma tabela com FK só pode ser criada depois da tabela referenciada, e removida antes dela. Isso é um grafo dirigido; a ordem é uma **ordenação topológica**.

## 🛠️ Exemplo prático
**1. Separando o banco de exemplo em arquivos**

Começamos pelo `loja.sql` (aula 03) dividido em schema e seed:
```bash
mkdir -p projeto/sql && cd projeto/sql
cp ../../recursos/sql/loja.sql .
awk '/^INSERT INTO categories/ {exit} {print}' loja.sql > 01_schema.sql
awk 'f {print} /^INSERT INTO categories/ && !f {f=1; print}' loja.sql > 02_seed.sql
grep -c "CREATE TABLE" 01_schema.sql; grep -c "^INSERT INTO" 02_seed.sql
```
```text
8
8
```
(O `awk` copia até o primeiro `INSERT` para o schema e, a partir dele, para o seed. No seu projeto você mantém os dois arquivos diretamente.)

**2. Índices, views e função**
```sql
CREATE INDEX IF NOT EXISTS products_category_id_idx    ON products (category_id);
CREATE INDEX IF NOT EXISTS products_active_price_idx   ON products (price, id) WHERE is_active;
CREATE INDEX IF NOT EXISTS orders_user_id_created_idx  ON orders (user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS order_items_product_id_idx  ON order_items (product_id);
CREATE INDEX IF NOT EXISTS cart_items_product_id_idx   ON cart_items (product_id);
CREATE INDEX IF NOT EXISTS users_email_lower_idx       ON users (lower(email));
-- order_items.order_id já é coberto pelo UNIQUE (order_id, product_id)
ANALYZE;
```
```sql
CREATE OR REPLACE VIEW v_catalog AS
SELECT p.id, p.sku, p.name, c.name AS category, p.price, p.stock
FROM products p JOIN categories c ON c.id = p.category_id
WHERE p.is_active AND p.stock > 0;

CREATE OR REPLACE VIEW v_order_summary AS
SELECT o.id, o.created_at, o.status, u.name AS customer, u.email,
       count(oi.id) AS items, coalesce(sum(oi.quantity), 0) AS units, o.total
FROM orders o JOIN users u ON u.id = o.user_id LEFT JOIN order_items oi ON oi.order_id = o.id
GROUP BY o.id, u.id;

DROP MATERIALIZED VIEW IF EXISTS mv_sales_by_month;
CREATE MATERIALIZED VIEW mv_sales_by_month AS
SELECT date_trunc('month', created_at)::date AS month,
       count(*) AS orders_created,
       count(*) FILTER (WHERE status = 'paid') AS orders_paid,
       coalesce(sum(total) FILTER (WHERE status = 'paid'), 0) AS revenue
FROM orders GROUP BY 1;
CREATE UNIQUE INDEX mv_sales_by_month_month_idx ON mv_sales_by_month (month);   -- exigido por REFRESH ... CONCURRENTLY
```
```sql
CREATE OR REPLACE FUNCTION fn_create_order(p_user_id integer) RETURNS integer
LANGUAGE plpgsql AS $$
DECLARE
    v_order_id integer;
    v_total    numeric(12,2);
    r          record;
BEGIN
    SELECT sum(ci.quantity * p.price) INTO v_total
    FROM carts c JOIN cart_items ci ON ci.cart_id = c.id JOIN products p ON p.id = ci.product_id
    WHERE c.user_id = p_user_id;

    IF v_total IS NULL THEN
        RAISE EXCEPTION 'carrinho vazio para o usuario %', p_user_id;
    END IF;

    INSERT INTO orders (user_id, status, total) VALUES (p_user_id, 'pending', v_total) RETURNING id INTO v_order_id;

    FOR r IN
        SELECT ci.product_id, ci.quantity, p.price
        FROM carts c JOIN cart_items ci ON ci.cart_id = c.id JOIN products p ON p.id = ci.product_id
        WHERE c.user_id = p_user_id ORDER BY ci.product_id           -- ordem fixa de travas: evita deadlock (aula 09)
    LOOP
        UPDATE products SET stock = stock - r.quantity WHERE id = r.product_id AND stock >= r.quantity;
        IF NOT FOUND THEN
            RAISE EXCEPTION 'estoque insuficiente para o produto %', r.product_id;   -- desfaz TUDO
        END IF;
        INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES (v_order_id, r.product_id, r.quantity, r.price);
    END LOOP;

    DELETE FROM cart_items WHERE cart_id IN (SELECT id FROM carts WHERE user_id = p_user_id);
    RETURN v_order_id;
END $$;
```
**3. A vistoria: `verify.sql`**
```sql
DO $$
DECLARE
    falhas text[] := '{}';
    total_checks integer := 0;
BEGIN
    total_checks := total_checks + 1;
    IF EXISTS (SELECT 1 FROM products WHERE stock < 0 OR price < 0) THEN
        falhas := array_append(falhas, 'produto com estoque ou preço negativo');
    END IF;

    total_checks := total_checks + 1;
    IF EXISTS (SELECT 1 FROM orders o JOIN (SELECT order_id, sum(quantity * unit_price) AS soma FROM order_items GROUP BY order_id) i
               ON i.order_id = o.id WHERE o.total <> i.soma) THEN
        falhas := array_append(falhas, 'total do pedido diverge da soma dos itens');
    END IF;

    total_checks := total_checks + 1;
    IF EXISTS (SELECT 1 FROM orders o WHERE NOT EXISTS (SELECT 1 FROM order_items oi WHERE oi.order_id = o.id)) THEN
        falhas := array_append(falhas, 'pedido sem itens');
    END IF;

    total_checks := total_checks + 1;
    IF EXISTS (SELECT 1 FROM orders o WHERE o.status = 'paid'
               AND NOT EXISTS (SELECT 1 FROM payments p WHERE p.order_id = o.id AND p.status = 'approved')) THEN
        falhas := array_append(falhas, 'pedido pago sem pagamento aprovado');
    END IF;

    total_checks := total_checks + 1;
    IF EXISTS (SELECT 1 FROM payments p JOIN orders o ON o.id = p.order_id WHERE p.status = 'approved' AND o.status <> 'paid') THEN
        falhas := array_append(falhas, 'pagamento aprovado em pedido que não está pago');
    END IF;

    total_checks := total_checks + 1;
    IF (SELECT count(*) FROM products) < 50 OR (SELECT count(*) FROM categories) < 5 THEN
        falhas := array_append(falhas, 'seed incompleto (esperado: >= 50 produtos e >= 5 categorias)');
    END IF;

    IF cardinality(falhas) > 0 THEN
        RAISE EXCEPTION 'verificação FALHOU (% de %): %', cardinality(falhas), total_checks, array_to_string(falhas, '; ');
    END IF;
    RAISE NOTICE 'verify: as % verificações passaram', total_checks;
END $$;
```
**4. O script que recria tudo**
```bash
#!/usr/bin/env bash
# Recria o banco do zero e aplica todos os arquivos, em ordem. Uso: ./run_all.sh [nome_do_banco]
set -euo pipefail
DB="${1:-loja}"
CONTAINER="${PG_CONTAINER:-minishop-pg}"
pg() { docker exec -i "$CONTAINER" psql -U postgres -X -q -v ON_ERROR_STOP=1 "$@"; }

pg -c "DROP DATABASE IF EXISTS $DB WITH (FORCE)" -c "CREATE DATABASE $DB"
for arquivo in 01_schema 02_seed 03_indices 04_views 05_funcoes verify; do
    echo "-> $arquivo.sql"
    pg -d "$DB" < "$arquivo.sql"
done
echo "OK: banco '$DB' pronto"
```
```bash
cd projeto/sql
chmod +x run_all.sh
./run_all.sh 2>&1
echo "código de saída: $?"
```
```text
-> 01_schema.sql
-> 02_seed.sql
-> 03_indices.sql
-> 04_views.sql
NOTICE:  materialized view "mv_sales_by_month" does not exist, skipping
-> 05_funcoes.sql
-> verify.sql
NOTICE:  verify: as 6 verificações passaram
OK: banco 'loja' pronto
código de saída: 0
```
`ON_ERROR_STOP=1` faz o `psql` parar no primeiro erro, e `set -euo pipefail` faz o script parar também: **scripts de banco não devem “continuar mesmo com erro”**.

**5. Usando as views e a função**
```sql
SELECT * FROM v_catalog ORDER BY price DESC LIMIT 3;
SELECT id, status, customer, items, units, total FROM v_order_summary ORDER BY id LIMIT 4;
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_sales_by_month;
SELECT * FROM mv_sales_by_month ORDER BY month LIMIT 4;
```
```text
 id |  sku  |            name            | category  |  price  | stock 
----+-------+----------------------------+-----------+---------+-------
 24 | MN-04 | Monitor 27 polegadas 4K    | Monitores | 2199.00 |     5
 25 | MN-05 | Monitor curvo 32 polegadas | Monitores | 1899.00 |    12
 23 | MN-03 | Monitor 27 polegadas QHD   | Monitores | 1399.00 |    38
(3 rows)

 id |  status   |  customer  | items | units | total  
----+-----------+------------+-------+-------+--------
  1 | pending   | Ana Souza  |     1 |     1 |  33.16
  2 | paid      | Ana Souza  |     1 |     3 |  99.48
  3 | paid      | Bruno Lima |     2 |     3 | 483.35
  4 | cancelled | Bruno Lima |     1 |     2 |  66.32
(4 rows)

   month    | orders_created | orders_paid | revenue 
------------+----------------+-------------+---------
 2026-02-01 |              1 |           0 |       0
 2026-03-01 |              3 |           2 |  582.83
 2026-04-01 |              1 |           1 | 5639.85
 2026-05-01 |              2 |           2 | 7550.10
(4 rows)
```
```sql
BEGIN;
SELECT fn_create_order(2) AS pedido_criado;                -- carrinho do usuário 2 (2 itens)
SELECT id, status, total FROM orders WHERE id = (SELECT max(id) FROM orders);
SELECT product_id, quantity, unit_price FROM order_items WHERE order_id = (SELECT max(id) FROM orders) ORDER BY product_id;
ROLLBACK;
```
```text
 pedido_criado 
---------------
            19
(1 row)

 id | status  | total  
----+---------+--------
 19 | pending | 488.80
(1 row)

 product_id | quantity | unit_price 
------------+----------+------------
          3 |        1 |     329.00
          7 |        2 |      79.90
(2 rows)
```
```sql
-- falha por estoque: a função levanta exceção e NADA fica gravado
BEGIN;
UPDATE products SET stock = 0 WHERE id = 7;
SELECT fn_create_order(2);
ROLLBACK;
SELECT count(*) AS pedidos_pending_do_usuario_2 FROM orders WHERE user_id = 2 AND status = 'pending';
```
```text
 pedidos_pending_do_usuario_2 
------------------------------
                            1
(1 row)

ERROR:  estoque insuficiente para o produto 7
CONTEXT:  PL/pgSQL function fn_create_order(integer) line 24 at RAISE
```
**6. A vistoria detecta corrupção**
```bash
cd projeto/sql
PSQL="docker exec -i minishop-pg psql -U postgres -d loja -X -q"
$PSQL -c "UPDATE orders SET total = total + 1 WHERE id = 1"          # corrompe de propósito
$PSQL -v ON_ERROR_STOP=1 < verify.sql 2>&1 | head -n 3; echo "código de saída: ${PIPESTATUS[0]}"
$PSQL -c "UPDATE orders SET total = total - 1 WHERE id = 1"          # conserta
$PSQL -v ON_ERROR_STOP=1 < verify.sql 2>&1
```
```text
ERROR:  verificação FALHOU (1 de 6): total do pedido diverge da soma dos itens
CONTEXT:  PL/pgSQL function inline_code_block line 39 at RAISE
código de saída: 3
NOTICE:  verify: as 6 verificações passaram
```
Em CI (Módulo 12), esse script pode rodar a cada *pull request*: se alguém quebrar o seed, a pipeline falha.

**7. Backup e restauração (e a prova de que funciona)**
```bash
cd projeto/sql
docker exec minishop-pg pg_dump -U postgres -Fc loja > loja.dump
ls -lh loja.dump | awk '{print "backup:", $5}'
docker exec minishop-pg psql -U postgres -X -q -c "DROP DATABASE IF EXISTS loja_restore WITH (FORCE)" -c "CREATE DATABASE loja_restore"
docker exec -i minishop-pg pg_restore -U postgres -d loja_restore --no-owner < loja.dump
for db in loja loja_restore; do
  docker exec minishop-pg psql -U postgres -d $db -X -t -A -c "SELECT '$db: ' || (SELECT count(*) FROM products) || ' produtos, ' || (SELECT count(*) FROM orders) || ' pedidos, soma dos totais = ' || (SELECT sum(total) FROM orders)"
done
docker exec minishop-pg psql -U postgres -X -q -c "DROP DATABASE loja_restore WITH (FORCE)"
```
```text
backup: 28K
loja: 50 produtos, 18 pedidos, soma dos totais = 37737.96
loja_restore: 50 produtos, 18 pedidos, soma dos totais = 37737.96
NOTICE:  database "loja_restore" does not exist, skipping
```
Os números idênticos nos dois bancos são a **prova** de que o backup restaura. Backup que nunca foi restaurado é uma esperança, não um backup. (Em produção: automatizar, guardar fora da máquina e testar a restauração periodicamente. Para um backup só do schema: `pg_dump -s`.)

## ⚠️ Erros comuns e boas práticas
| Mensagem / sintoma | Causa | Solução |
|---|---|---|
| `ERROR: database "loja" is being accessed by other users` | Conexões abertas ao tentar `DROP DATABASE` | `DROP DATABASE ... WITH (FORCE)` (PG ≥ 13) ou feche as conexões |
| Script aplica metade e “segue em frente” | Sem `ON_ERROR_STOP` | `psql -v ON_ERROR_STOP=1` + `set -e` |
| `ERROR: relation "x" already exists` ao reexecutar | Script não idempotente | `IF NOT EXISTS`, `CREATE OR REPLACE`, ou recriar o banco |
| `pg_restore: error: ... role "x" does not exist` | Dump com donos que não existem no destino | `--no-owner` (e `--no-privileges` se preciso) |
| `ERROR: cannot refresh materialized view "x" concurrently` | Falta índice `UNIQUE` | Crie um `UNIQUE INDEX` na view |
| Seed antigo quebra após mudar o schema | Dados e estrutura fora de sincronia | Mantenha o seed junto do schema e rode `verify.sql` sempre |
| Função com efeito colateral “escondido” | Lógica de negócio espalhada no banco | Decida: regra no código (ORM/serviço) **ou** na função; documente |

- **Versione** todos os `.sql` no Git; o banco é produto do código, não o contrário.
- Seeds com **dados fictícios** (nunca dados reais de clientes) e senhas de exemplo óbvias.
- Rode `verify.sql` depois de toda mudança de schema e depois de toda restauração.
- Regras no banco (constraints, FKs, funções) protegem de qualquer cliente; regras de negócio complexas costumam ficar na aplicação (testáveis, versionadas): escolha conscientemente.

## 🧠 Pausa para lógica
**Problema (ordem das tabelas).** Obtenha, a partir das chaves estrangeiras do banco, a ordem em que as tabelas podem ser **criadas** (pais antes de filhos) e a ordem de **remoção** (filhos antes de pais). Use o catálogo `pg_constraint` e `graphlib.TopologicalSorter`.

<details><summary>Dica</summary>
Cada FK é uma aresta “filha depende da pai”. <code>TopologicalSorter</code> recebe <code>{no: {dependências}}</code> e devolve uma ordem em que as dependências vêm antes. A ordem de remoção é a inversa.
</details>

<details><summary>Solução comentada</summary>

```bash
cd projeto/sql
docker exec minishop-pg psql -U postgres -d loja -X -t -A -F ' ' -c "
  SELECT conrelid::regclass, confrelid::regclass FROM pg_constraint WHERE contype = 'f' AND connamespace = 'public'::regnamespace
  UNION ALL SELECT tablename::regclass, tablename::regclass FROM pg_tables WHERE schemaname = 'public'" |
python -c "
import sys
from graphlib import TopologicalSorter

deps = {}
for linha in sys.stdin:
    filha, pai = linha.split()
    deps.setdefault(filha, set())
    if filha != pai:                     # a linha 'tabela tabela' só garante que toda tabela apareça no grafo
        deps[filha].add(pai)
ordem = list(TopologicalSorter(deps).static_order())
print('criar  :', ' -> '.join(ordem))
print('remover:', ' -> '.join(reversed(ordem)))
"
```
```text
criar  : categories -> users -> products -> carts -> orders -> cart_items -> order_items -> payments
remover: payments -> order_items -> cart_items -> orders -> carts -> products -> users -> categories
```
É a mesma ordem usada no `DROP TABLE IF EXISTS payments, order_items, orders, ...` do `loja.sql` (ou `CASCADE`, que resolve por você, mas apaga dependências sem avisar). O Django faz isso ao aplicar migrações. Se houver um ciclo de FKs, o `TopologicalSorter` levanta `CycleError`: um sinal para revisar o modelo.
</details>

**Variação mais difícil:** detecte e relate um ciclo de dependências (crie uma FK circular de teste) em vez de falhar com a exceção genérica.

## 🧩 Exercícios
**1. Fixação**
(a) Qual a diferença entre uma *view* e uma *materialized view*? (b) Por que um `pg_dump` sem teste de restauração não é um backup confiável? (c) O que `ON_ERROR_STOP` evita?

<details><summary>Solução</summary>

(a) View: consulta salva, sempre atual, sem armazenar dados; materializada: guarda o resultado, mais rápida, mas precisa de `REFRESH` e pode ficar desatualizada. (b) Pode estar corrompido, incompleto ou depender de recursos ausentes; só a restauração prova que funciona. (c) O `psql` continuar executando após um erro, deixando o banco em estado parcial.
</details>

**2. Aplicação no projeto MiniShop (entrega do módulo)**
Monte `projeto/sql/` completo e publique a versão `v0.3-banco-sql`.

Critérios de pronto:
- [ ] Os arquivos `01_schema.sql` a `05_funcoes.sql`, `verify.sql` e `run_all.sh` existem e `./run_all.sh` termina com `OK` em uma máquina limpa
- [ ] Você **escreveu seu próprio** seed de pelo menos 20 produtos (a partir do `seed/produtos.csv` do Módulo 1, convertido para `INSERT`s), com ≥ 3 usuários e ≥ 8 pedidos coerentes (totais batendo com os itens)
- [ ] `verify.sql` com **pelo menos 8 verificações** (acrescente: SKU/e-mail sem espaços, `payments.paid_at` preenchido quando aprovado, nenhum produto ativo sem categoria…) e você mostrou que ele **falha** ao corromper um dado
- [ ] Pelo menos 2 views e 1 *materialized view* úteis ao painel administrativo
- [ ] Os arquivos `consultas/` (aulas 04 a 06) e `exercicios/` (aula 07) rodam sem erro contra o banco criado
- [ ] `docs/banco.md` com: diagrama ER (Mermaid), como recriar o banco, como fazer e **testar** o backup, e as decisões (por que `NUMERIC`, por que `unit_price`, quais índices e por quê)
- [ ] Um teste Python (pytest + psycopg) que roda `run_all.sh` num banco `loja_teste` e confere contagens e a função `fn_create_order`
- [ ] Tag: `git tag v0.3-banco-sql && git push --tags`

<details><summary>Solução de referência (teste Python)</summary>

```python
import subprocess
import psycopg

def test_banco_reconstroi_e_funcao_de_pedido():
    subprocess.run(["./run_all.sh", "loja_teste"], cwd="projeto/sql", check=True, capture_output=True)
    with psycopg.connect("postgresql://postgres:dev@localhost:5432/loja_teste") as conn:
        assert conn.execute("SELECT count(*) FROM products").fetchone()[0] >= 50
        with conn.transaction(force_rollback=True):                    # desfaz no final
            pedido = conn.execute("SELECT fn_create_order(2)").fetchone()[0]
            assert conn.execute("SELECT total FROM orders WHERE id = %s", (pedido,)).fetchone()[0] > 0

test_banco_reconstroi_e_funcao_de_pedido()
print("teste passou")
```
```text
teste passou
```
(No seu repositório o teste fica em `tests/test_banco.py` e roda com `uv run pytest`.)
</details>

**3. Desafio (opcional)**
Escreva o `docker-compose.yml` mínimo com o PostgreSQL 18 e um volume, e um script que o sobe, espera ficar saudável (`pg_isready`) e roda o `run_all.sh`. (Prévia do Módulo 11.)

## 🎤 Na entrevista
- **Como você garante que qualquer pessoa recria o banco do projeto?** Schema e seed em arquivos SQL (ou migrações) versionados no Git, um script que recria do zero e para no primeiro erro, e uma verificação automática de integridade.
- **Qual a diferença entre `pg_dump` em formato SQL e em formato custom (`-Fc`)?** SQL é texto reaplicável com `psql`; custom é binário compactado, restaurado com `pg_restore`, permitindo restauração seletiva e paralela.
- **Quando usar uma view materializada?** Quando a consulta é pesada e o dado tolera pequeno atraso (relatórios, dashboards); atualiza-se com `REFRESH` (de preferência `CONCURRENTLY`, com índice único).
- **Como você testa se um backup serve?** Restaurando em um banco separado e comparando contagens/somas e rodando as verificações de integridade.

## 📚 Para ir além
- 📄 Documentação oficial: [`pg_dump`](https://www.postgresql.org/docs/current/app-pgdump.html). Formatos e opções de backup.
- 📄 Documentação oficial: [`pg_restore`](https://www.postgresql.org/docs/current/app-pgrestore.html). Restauração e `--no-owner`.
- 📄 Documentação oficial: [Views materializadas](https://www.postgresql.org/docs/current/rules-materializedviews.html). Quando usar e como atualizar.
- 📄 Documentação oficial: [PL/pgSQL](https://www.postgresql.org/docs/current/plpgsql.html). Linguagem de funções do PostgreSQL.
- 🏋️ Prática extra: simule um desastre: apague a tabela `orders` e restaure só ela do dump (`pg_restore -t orders`).

## ✅ Checklist da aula
- [ ] `./run_all.sh` recria o banco do zero e o `verify.sql` passa
- [ ] Mostrei o `verify.sql` falhando ao corromper um dado
- [ ] Fiz o backup e **restaurei** em outro banco com contagens iguais
- [ ] Documentei o banco em `docs/banco.md`
- [ ] Tag `v0.3-banco-sql` criada
