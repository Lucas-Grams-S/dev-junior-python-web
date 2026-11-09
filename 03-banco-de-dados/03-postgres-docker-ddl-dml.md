# 03. PostgreSQL com Docker, DDL e DML

> ⏱️ ~1h30 · Módulo 3 · Pré-requisitos: [01](01-por-que-banco-modelagem-er.md), [02](02-normalizacao.md)

## 🎯 Objetivos
Ao final desta aula você consegue:
- Subir um PostgreSQL 18 local em um container Docker e conectar com `psql`
- Usar os comandos principais do `psql` (`\l`, `\dt`, `\d`, `\i`, `\x`, `\timing`)
- Criar, alterar e remover tabelas (DDL) com tipos e constraints básicas
- Inserir, atualizar e apagar dados (DML), incluindo `RETURNING` e `ON CONFLICT`
- Carregar o banco de exemplo da loja e explicar o `NULL`

## 🤔 Por que isso importa
O PostgreSQL será o banco do MiniShop até o deploy na AWS (RDS). Saber subir e reiniciar o banco local em segundos, e escrever DDL/DML sem medo, é o dia a dia de um dev backend. Também é onde nascem os acidentes clássicos: `UPDATE` ou `DELETE` sem `WHERE`.

## 💡 Intuição (explicação simples)
- **Docker** = uma **caixa selada com o PostgreSQL já instalado e configurado**: você liga, usa e descarta, sem “sujar” o seu computador (o Módulo 11 explica o Docker a fundo).
- **DDL** (*Data Definition Language*) = **construir e reformar o armário** (`CREATE`, `ALTER`, `DROP`). **DML** (*Data Manipulation Language*) = **guardar, trocar e tirar coisas das gavetas** (`INSERT`, `UPDATE`, `DELETE`). **DQL** = **olhar** o que há lá (`SELECT`, aula 04).

## 🔬 Como funciona por dentro
- O PostgreSQL é um **servidor** (processo que escuta na porta 5432, aula 2.01). Você fala com ele por um **cliente**: o `psql` (linha de comando), uma biblioteca (`psycopg`, aula 10) ou o ORM do Django.
- Um servidor tem vários **bancos** (databases); cada banco tem **schemas** (o padrão é `public`) que contêm tabelas.
- Os dados ficam em arquivos no disco do servidor. No container, para que sobrevivam à remoção dele, guardamos o diretório de dados em um **volume** do Docker (`-v minishop_pgdata:/var/lib/postgresql`).
- Cada comando SQL termina em `;`. Palavras-chave não diferenciam maiúsculas; **textos** entre aspas simples (`'abc'`) diferenciam. Aspas duplas são para identificadores.
- **Tipos principais:**

| Tipo | Uso | Exemplo |
|---|---|---|
| `integer` / `bigint` | inteiros (4 / 8 bytes) | `stock` / ids grandes |
| `numeric(p,s)` | decimal exato | `numeric(10,2)` = até 10 dígitos, 2 decimais (dinheiro) |
| `text` | texto de tamanho livre | `name` |
| `boolean` | `true` / `false` / `NULL` | `is_active` |
| `timestamptz` | data e hora com fuso (guardada em UTC) | `created_at` |
| `date` | só a data | `birth_date` |
| `uuid` | identificador universal | ids públicos |
| `jsonb` | JSON consultável | metadados |

- `GENERATED ALWAYS AS IDENTITY` gera o `id` automaticamente (o padrão moderno; substitui `serial`).
- **`NULL`** significa “valor ausente/desconhecido”, **não** zero nem vazio. Ele infecta as comparações: `NULL = NULL` não é verdadeiro (nem falso), é *desconhecido* (lógica de três valores). Use `IS NULL`.

## 🛠️ Exemplo prático
**1. Subindo o PostgreSQL** (comandos executados pelo autor; rode no seu terminal)
```bash
docker run --name minishop-pg \
  -e POSTGRES_PASSWORD=dev \
  -p 127.0.0.1:5432:5432 \
  -v minishop_pgdata:/var/lib/postgresql \
  -d postgres:18
```
- `--name`: nome do container · `-e`: variável de ambiente com a senha do usuário `postgres` (**só para desenvolvimento**) · `-p 127.0.0.1:5432:5432`: publica a porta **apenas** na sua máquina (não na rede) · `-v`: volume para os dados · `-d`: em segundo plano · `postgres:18`: a imagem.
- Na primeira vez o Docker baixa a imagem (~650 MB).
```bash
docker ps --filter name=minishop-pg --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'
docker exec minishop-pg pg_isready -U postgres
```
```text
NAMES         IMAGE         STATUS         PORTS
minishop-pg   postgres:18   Up 2 minutes   127.0.0.1:5432->5432/tcp
/var/run/postgresql:5432 - accepting connections
```
Dia a dia: `docker stop minishop-pg` / `docker start minishop-pg` / `docker logs minishop-pg` / `docker rm -f minishop-pg` (o volume mantém os dados; para apagar tudo: `docker volume rm minishop_pgdata`).

**2. Conectando com o `psql`**
```bash
docker exec -it minishop-pg psql -U postgres        # abre o console interativo
```
Dentro dele, os comandos que começam com `\` são do `psql`, não SQL:

| Comando | Faz |
|---|---|
| `\l` | lista os bancos |
| `\c loja` | conecta ao banco `loja` |
| `\dt` | lista as tabelas · `\d produtos` descreve uma tabela |
| `\x` | alterna a saída expandida (uma coluna por linha) |
| `\timing` | mostra o tempo de cada comando |
| `\i arquivo.sql` | executa um arquivo SQL |
| `\q` | sai |

Daqui em diante, os blocos SQL mostram o que você digitaria no `psql` e a saída real. (Para executar um comando só, sem entrar: `docker exec minishop-pg psql -U postgres -d loja -c "SELECT 1"`.)

**3. DDL: criando as primeiras tabelas**
```sql
CREATE TABLE categories (
    id    integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name  text NOT NULL UNIQUE,
    slug  text NOT NULL UNIQUE
);

CREATE TABLE products (
    id           integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    category_id  integer       NOT NULL REFERENCES categories (id),
    sku          text          NOT NULL UNIQUE,
    name         text          NOT NULL,
    price        numeric(10,2) NOT NULL CHECK (price >= 0),
    stock        integer       NOT NULL DEFAULT 0 CHECK (stock >= 0),
    is_active    boolean       NOT NULL DEFAULT true,
    created_at   timestamptz   NOT NULL DEFAULT now()
);

\dt
\d products
```
```text
             List of tables
 Schema |    Name    | Type  |  Owner   
--------+------------+-------+----------
 public | categories | table | postgres
 public | products   | table | postgres
(2 rows)

                                   Table "public.products"
   Column    |           Type           | Collation | Nullable |           Default            
-------------+--------------------------+-----------+----------+------------------------------
 id          | integer                  |           | not null | generated always as identity
 category_id | integer                  |           | not null | 
 sku         | text                     |           | not null | 
 name        | text                     |           | not null | 
 price       | numeric(10,2)            |           | not null | 
 stock       | integer                  |           | not null | 0
 is_active   | boolean                  |           | not null | true
 created_at  | timestamp with time zone |           | not null | now()
Indexes:
    "products_pkey" PRIMARY KEY, btree (id)
    "products_sku_key" UNIQUE CONSTRAINT, btree (sku)
Check constraints:
    "products_price_check" CHECK (price >= 0::numeric)
    "products_stock_check" CHECK (stock >= 0)
Foreign-key constraints:
    "products_category_id_fkey" FOREIGN KEY (category_id) REFERENCES categories(id)
```
Cada coluna tem **tipo** e **restrições**: `NOT NULL` (obrigatória), `UNIQUE`, `CHECK (expressão)`, `DEFAULT`, `REFERENCES` (chave estrangeira). O aprofundamento está na aula 08.

**4. DDL: alterar e remover**
```sql
ALTER TABLE products ADD COLUMN description text NOT NULL DEFAULT '';
ALTER TABLE products RENAME COLUMN description TO details;
ALTER TABLE products ALTER COLUMN name TYPE varchar(120);
ALTER TABLE products DROP COLUMN details;
CREATE TABLE temporaria (x int);
DROP TABLE temporaria;
DROP TABLE IF EXISTS temporaria;      -- sem erro se não existir
\d products
```
```text
                                   Table "public.products"
   Column    |           Type           | Collation | Nullable |           Default            
-------------+--------------------------+-----------+----------+------------------------------
 id          | integer                  |           | not null | generated always as identity
 category_id | integer                  |           | not null | 
 sku         | text                     |           | not null | 
 name        | character varying(120)   |           | not null | 
 price       | numeric(10,2)            |           | not null | 
 stock       | integer                  |           | not null | 0
 is_active   | boolean                  |           | not null | true
 created_at  | timestamp with time zone |           | not null | now()
Indexes:
    "products_pkey" PRIMARY KEY, btree (id)
    "products_sku_key" UNIQUE CONSTRAINT, btree (sku)
Check constraints:
    "products_price_check" CHECK (price >= 0::numeric)
    "products_stock_check" CHECK (stock >= 0)
Foreign-key constraints:
    "products_category_id_fkey" FOREIGN KEY (category_id) REFERENCES categories(id)

NOTICE:  table "temporaria" does not exist, skipping
```
Em produção você **não** altera tabelas à mão: usa **migrações** versionadas (aula 11 e Módulo 5), para o time e os ambientes ficarem iguais.

**5. DML: INSERT**
```sql
INSERT INTO categories (name, slug) VALUES ('Periféricos', 'perifericos'), ('Áudio', 'audio');

INSERT INTO products (category_id, sku, name, price, stock)
VALUES (1, 'PF-01', 'Mouse sem fio', 89.90, 12),
       (1, 'PF-02', 'Teclado mecânico', 329.00, 5),
       (2, 'AU-01', 'Fone Bluetooth', 249.90, 0)
RETURNING id, sku, created_at::date AS criado;      -- devolve as linhas inseridas (com o id gerado!)
```
```text
 id |  sku  |   criado   
----+-------+------------
  1 | PF-01 | 2026-11-08
  2 | PF-02 | 2026-11-08
  3 | AU-01 | 2026-11-08
(3 rows)
```
O `RETURNING` evita um `SELECT` extra para descobrir o `id` gerado. Aplicações usam isso o tempo todo.

**6. DML: UPDATE e DELETE (sempre com `WHERE`!)**
```sql
UPDATE products SET price = price * 1.10 WHERE sku = 'PF-01' RETURNING sku, price;
UPDATE products SET stock = stock + 20, is_active = true WHERE category_id = 2 RETURNING sku, stock;
DELETE FROM products WHERE sku = 'PF-02' RETURNING id, sku;
SELECT id, sku, name, price, stock FROM products ORDER BY id;
```
```text
  sku  | price 
-------+-------
 PF-01 | 98.89
(1 row)

  sku  | stock 
-------+-------
 AU-01 |    20
(1 row)

 id |  sku  
----+-------
  2 | PF-02
(1 row)

 id |  sku  |      name      | price  | stock 
----+-------+----------------+--------+-------
  1 | PF-01 | Mouse sem fio  |  98.89 |    12
  3 | AU-01 | Fone Bluetooth | 249.90 |    20
(2 rows)
```
**7. A rede de segurança: transação manual**

Antes de um `UPDATE`/`DELETE` perigoso, abra uma transação e confira o estrago antes de confirmar (a aula 09 explica transações):
```sql
BEGIN;
UPDATE products SET price = 0;                 -- esqueceu o WHERE!
SELECT sku, price FROM products ORDER BY id;
ROLLBACK;                                       -- desfaz tudo
SELECT sku, price FROM products ORDER BY id;
```
```text
  sku  | price 
-------+-------
 PF-01 |  0.00
 AU-01 |  0.00
(2 rows)

  sku  | price  
-------+--------
 PF-01 |  98.89
 AU-01 | 249.90
(2 rows)
```
Hábito de profissional: em produção, rode primeiro um `SELECT` com o mesmo `WHERE` para ver quantas linhas serão afetadas.

**8. `INSERT ... ON CONFLICT` (upsert) e idempotência**
```sql
INSERT INTO categories (name, slug) VALUES ('Áudio', 'audio'), ('Monitores', 'monitores')
ON CONFLICT (slug) DO NOTHING;                  -- 'audio' já existe: ignora, não dá erro

INSERT INTO products (category_id, sku, name, price, stock)
VALUES (2, 'AU-01', 'Fone Bluetooth', 259.90, 7)
ON CONFLICT (sku) DO UPDATE SET price = EXCLUDED.price, stock = products.stock + EXCLUDED.stock
RETURNING sku, price, stock;

SELECT id, name FROM categories ORDER BY id;
```
```text
  sku  | price  | stock 
-------+--------+-------
 AU-01 | 259.90 |    27
(1 row)

 id |    name     
----+-------------
  1 | Periféricos
  2 | Áudio
  4 | Monitores
(3 rows)
```
`EXCLUDED` é a linha que você tentou inserir. Com `ON CONFLICT`, rodar o script duas vezes dá o mesmo resultado: **idempotência**, essencial em seeds e em webhooks (Módulo 7).

**9. `NULL` na prática**
```sql
SELECT NULL = NULL AS igual, NULL IS NULL AS eh_nulo, NULL + 1 AS soma, coalesce(NULL, 'padrão') AS com_padrao;
SELECT 5 AS n, pg_typeof(5) AS tipo_n, pg_typeof(5.0) AS tipo_decimal, pg_typeof('a'::text) AS tipo_texto, '42'::int + 1 AS cast_;
```
```text
 igual | eh_nulo | soma | com_padrao 
-------+---------+------+------------
       | t       |      | padrão
(1 row)

 n | tipo_n  | tipo_decimal | tipo_texto | cast_ 
---+---------+--------------+------------+-------
 5 | integer | numeric      | text       |    43
(1 row)
```
(O `psql` mostra `NULL` como célula vazia; no resultado acima, `igual` e `soma` são `NULL`.)

**10. Carregando o banco de exemplo da loja**

O arquivo `recursos/sql/loja.sql` (deste curso) recria as 8 tabelas do MiniShop com dados de exemplo: 5 categorias, 50 produtos, 6 usuários, 18 pedidos. Copie-o para o seu projeto (`projeto/sql/loja.sql`) e carregue:
```bash
docker exec minishop-pg psql -U postgres -X -q -c "DROP DATABASE IF EXISTS loja WITH (FORCE)" -c "CREATE DATABASE loja"
docker exec -i minishop-pg psql -U postgres -d loja -X -q < recursos/sql/loja.sql
docker exec minishop-pg psql -U postgres -d loja -X -c '\dt'
```
```text
             List of tables
 Schema |    Name     | Type  |  Owner   
--------+-------------+-------+----------
 public | cart_items  | table | postgres
 public | carts       | table | postgres
 public | categories  | table | postgres
 public | order_items | table | postgres
 public | orders      | table | postgres
 public | payments    | table | postgres
 public | products    | table | postgres
 public | users       | table | postgres
(8 rows)
```
```sql
\c loja
SELECT (SELECT count(*) FROM categories) AS categorias, (SELECT count(*) FROM products) AS produtos,
       (SELECT count(*) FROM users) AS usuarios, (SELECT count(*) FROM orders) AS pedidos;
```
```text
 categorias | produtos | usuarios | pedidos 
------------+----------+----------+---------
          5 |       50 |        6 |      18
(1 row)
```
Este é o banco que usaremos nas aulas 04 a 11. Se bagunçar tudo, repita o comando acima: o script começa apagando e recriando as tabelas.

## ⚠️ Erros comuns e boas práticas
| Mensagem | Causa | Solução |
|---|---|---|
| `psql: error: connection to server ... failed: Connection refused` | Container parado | `docker start minishop-pg`; confira `docker ps` |
| `FATAL: password authentication failed for user "postgres"` | Senha diferente da usada na criação | Use a do `POSTGRES_PASSWORD` (a variável só vale na 1ª criação do volume) |
| `ERROR: relation "produtos" does not exist` | Tabela com outro nome/schema, ou banco errado | `\dt`, `\c loja` |
| `ERROR: null value in column "name" of relation "products" violates not-null constraint` | Faltou valor obrigatório | Informe a coluna |
| `ERROR: duplicate key value violates unique constraint "products_sku_key"` | SKU repetido | Outro valor, ou `ON CONFLICT` |
| `ERROR: new row for relation "products" violates check constraint "products_price_check"` | Regra `CHECK` violada | Corrija o dado |
| `ERROR: insert or update on table "products" violates foreign key constraint` | Categoria inexistente | Cadastre a categoria antes |
| `ERROR: syntax error at or near "..."` | Erro de sintaxe (vírgula sobrando, falta `;`) | Leia o ponto indicado **e** a linha anterior |
| `docker: Error response ... port is already allocated` | Outro serviço usa a 5432 | Pare-o ou use `-p 127.0.0.1:5433:5432` |

- **Nunca** exponha o PostgreSQL à internet com senha fraca (`-p 5432:5432` publica em todas as interfaces; prefira `127.0.0.1:`).
- Sempre `WHERE` em `UPDATE`/`DELETE`; teste com `SELECT` e `BEGIN ... ROLLBACK`.
- Dinheiro em `numeric`; datas em `timestamptz`; ids com `IDENTITY`.
- Guarde o DDL/seed em arquivos `.sql` versionados no Git, não só na sua memória.

## 🧠 Pausa para lógica
**Problema (seed idempotente).** O script de seed insere 3 produtos. Se for executado duas vezes, não pode duplicar nem falhar. Escreva o SQL e a versão equivalente em Python usando um `dict`/`set` de SKUs já vistos.

<details><summary>Dica</summary>
Em SQL, <code>ON CONFLICT (sku) DO NOTHING</code>. Em Python, teste <code>if sku in existentes</code> antes de inserir.
</details>

<details><summary>Solução comentada</summary>

```sql
CREATE TEMP TABLE seed_demo (sku text PRIMARY KEY, name text);
INSERT INTO seed_demo VALUES ('A', 'Mouse'), ('B', 'Teclado'), ('C', 'Cabo') ON CONFLICT (sku) DO NOTHING;
INSERT INTO seed_demo VALUES ('A', 'Mouse'), ('B', 'Teclado'), ('C', 'Cabo') ON CONFLICT (sku) DO NOTHING;
SELECT count(*) AS linhas FROM seed_demo;
```
```text
 linhas 
--------
      3
(1 row)
```
```python
existentes = {}
def seed(itens):
    inseridos = 0
    for sku, nome in itens:
        if sku not in existentes:        # equivale ao ON CONFLICT DO NOTHING
            existentes[sku] = nome
            inseridos += 1
    return inseridos

dados = [("A", "Mouse"), ("B", "Teclado"), ("C", "Cabo")]
print(seed(dados), seed(dados), len(existentes))
```
```text
3 0 3
```
Duas execuções, mesmo estado final: é isso que torna scripts e webhooks seguros para repetir. (Em um banco real, o `ON CONFLICT` é melhor que o teste em Python porque é atômico: duas execuções simultâneas não duplicam.)
</details>

**Variação mais difícil:** e se o SKU existir com **nome diferente**? Escreva a regra para atualizar o nome (upsert) e conte quantas linhas foram inseridas e quantas atualizadas (`xmax = 0` indica inserção em um `RETURNING`; pesquise).

## 🧩 Exercícios
**1. Fixação**
Qual comando (a) lista as tabelas; (b) mostra a estrutura de `orders`; (c) liga o cronômetro; (d) executa um arquivo `x.sql`? E qual a diferença entre `DELETE FROM t` e `DROP TABLE t`?

<details><summary>Solução</summary>

(a) `\dt` (b) `\d orders` (c) `\timing` (d) `\i x.sql` (ou `psql -f x.sql`). `DELETE FROM t` apaga as **linhas** (a tabela continua; pode ser desfeito numa transação); `DROP TABLE t` apaga a **tabela inteira** (estrutura e dados). `TRUNCATE t` esvazia rapidamente.
</details>

**2. Aplicação no projeto MiniShop**
Monte o ambiente de banco do projeto.

Critérios de pronto:
- [ ] Container `minishop-pg` rodando com volume e porta presa em `127.0.0.1`
- [ ] Arquivo `projeto/sql/loja.sql` no repositório e banco `loja` carregado (`\dt` mostra 8 tabelas)
- [ ] `README` do projeto com os comandos para subir/parar o banco e recarregar o seed
- [ ] Você criou uma tabela nova `reviews (id, product_id FK, user_id FK, rating 1–5 com CHECK, comment, created_at)` em `projeto/sql/extras.sql` e inseriu 3 avaliações com `RETURNING`
- [ ] Teste de segurança: um `UPDATE` sem `WHERE` dentro de `BEGIN ... ROLLBACK` que você desfez
- [ ] Commit `feat: add postgres setup and extra reviews table`

<details><summary>Solução de referência</summary>

```sql
\c loja
CREATE TABLE reviews (
    id          integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    product_id  integer     NOT NULL REFERENCES products (id) ON DELETE CASCADE,
    user_id     integer     NOT NULL REFERENCES users (id),
    rating      smallint    NOT NULL CHECK (rating BETWEEN 1 AND 5),
    comment     text,
    created_at  timestamptz NOT NULL DEFAULT now(),
    UNIQUE (product_id, user_id)                   -- um usuário avalia um produto uma vez
);
INSERT INTO reviews (product_id, user_id, rating, comment)
VALUES (1, 1, 5, 'Ótimo'), (1, 2, 4, NULL), (3, 1, 2, 'Caro')
RETURNING id, product_id, rating;
```
```text
 id | product_id | rating 
----+------------+--------
  1 |          1 |      5
  2 |          1 |      4
  3 |          3 |      2
(3 rows)
```
</details>

**3. Desafio (opcional)**
Suba um **segundo** container PostgreSQL na porta 5433 (`minishop-pg-test`) para os testes automatizados, e carregue o mesmo `loja.sql`. Para que serve ter um banco separado para testes?

## 🎤 Na entrevista
- **Qual a diferença entre DDL, DML e DQL?** DDL define estrutura (`CREATE`, `ALTER`, `DROP`); DML manipula dados (`INSERT`, `UPDATE`, `DELETE`); DQL consulta (`SELECT`).
- **O que é `NULL` e por que `= NULL` não funciona?** Ausência de valor; qualquer comparação com `NULL` resulta em desconhecido; use `IS NULL`/`IS NOT NULL`.
- **Qual a diferença entre `DELETE`, `TRUNCATE` e `DROP`?** `DELETE` remove linhas (com `WHERE`, em transação); `TRUNCATE` esvazia a tabela rapidamente; `DROP` remove a tabela.
- **O que é `ON CONFLICT` / upsert?** Insere e, se violar uma restrição única, ignora ou atualiza; torna a operação idempotente e atômica.

## 📚 Para ir além
- 📄 Documentação oficial: [Imagem `postgres` (Docker Hub)](https://hub.docker.com/_/postgres). Variáveis de ambiente, volumes e versões (veja a nota sobre o diretório de dados na versão 18).
- 📄 Documentação oficial: [`psql`](https://www.postgresql.org/docs/current/app-psql.html). Todos os meta-comandos.
- 📄 Documentação oficial: [Tipos numéricos](https://www.postgresql.org/docs/current/datatype-numeric.html). `numeric`, `integer` e identidade.
- 📄 Documentação oficial: [Constraints](https://www.postgresql.org/docs/current/ddl-constraints.html). Referência para o que usamos nas tabelas.
- 🏋️ Prática extra: crie a tabela `coupons (code, percent, valid_until)` com as restrições adequadas e 3 cupons.

## ✅ Checklist da aula
- [ ] PostgreSQL rodando em Docker e conexão com `psql`
- [ ] Criei, alterei e removi tabelas
- [ ] Usei `RETURNING`, `ON CONFLICT` e `BEGIN/ROLLBACK`
- [ ] Banco `loja` carregado a partir de `loja.sql`
