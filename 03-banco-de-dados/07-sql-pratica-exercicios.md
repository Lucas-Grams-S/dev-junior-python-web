# 07. SQL na prática: lista de exercícios com as consultas da loja

> ⏱️ ~1h30 · Módulo 3 · Pré-requisitos: [04](04-select-where-order-limit.md), [05](05-joins.md), [06](06-group-by-subqueries.md)

## 🎯 Objetivos
Ao final desta aula você consegue:
- Traduzir perguntas de negócio em consultas SQL corretas
- Combinar filtros, joins, agregações, subconsultas, CTEs e funções de janela
- Validar o resultado de uma consulta (contagens, totais, casos de borda)
- Escrever atualizações seguras dentro de transações
- Pensar em **conjuntos** de linhas, e não em laços linha a linha

## 🤔 Por que isso importa
SQL só se aprende escrevendo. Em entrevistas de backend/dados e no trabalho, a pergunta é sempre “qual consulta responde isto?”. Esta aula é uma bateria de 19 exercícios sobre o banco da loja, do simples ao difícil, para você ganhar fluência antes de entrar em índices, transações e ORM.

## 💡 Intuição (explicação simples)
É como aprender uma língua: ler regras não basta, é preciso **conversar**. Cada exercício é uma pergunta que um colega de negócio faria (“quais produtos nunca venderam?”). Primeiro tente sozinho; olhe a solução só depois de uma tentativa real e compare o **resultado**, não o texto: existem várias consultas corretas.

## 🔬 Como funciona por dentro
**Método de resolução em 5 passos** (use em todo exercício):

1. **Entenda a pergunta** e o formato esperado (colunas, ordem, quantas linhas).
2. **Ache as tabelas** (ER da aula 01) e o caminho de joins.
3. **Escolha a granularidade**: o que é uma linha do resultado? (um produto? um pedido? um mês?) Isso define o `GROUP BY`.
4. **Construa por camadas**: comece com `SELECT * ... LIMIT 5`, junte, filtre, agregue.
5. **Valide**: o total bate com outra forma de calcular? O caso sem dados (zero) funciona? Há linhas duplicadas por join?

**Pensar em conjuntos:** em vez de “para cada pedido, some os itens” (laço), diga “agrupe os itens por pedido e some”. O banco otimiza a operação inteira.

## 🛠️ Exemplo prático
**Preparação:** banco `loja` carregado (`recursos/sql/loja.sql`). Abra o `psql` (`docker exec -it minishop-pg psql -U postgres -d loja`) e use `\timing`.

Um exemplo resolvido para calibrar o nível (**“Quanto cada cliente gastou em pedidos pagos, com a participação no total?”**):
```sql
WITH gasto AS (
    SELECT u.id, u.name, sum(o.total) AS gasto
    FROM users u JOIN orders o ON o.user_id = u.id AND o.status = 'paid'
    GROUP BY u.id, u.name
)
SELECT name, gasto, round(100 * gasto / sum(gasto) OVER (), 1) AS pct_do_total,
       rank() OVER (ORDER BY gasto DESC) AS posicao
FROM gasto ORDER BY posicao;
```
```text
     name     |  gasto   | pct_do_total | posicao 
--------------+----------+--------------+---------
 Diego Alves  | 18309.40 |         55.7 |       1
 Bruno Lima   | 12234.50 |         37.2 |       2
 Carla Mendes |  1289.30 |          3.9 |       3
 Ana Souza    |  1032.68 |          3.1 |       4
(4 rows)
```
Granularidade: **um cliente por linha**. A janela `sum(gasto) OVER ()` soma todos sem colapsar as linhas.

### Bloco A: consultas simples
**A1.** Produtos ativos com estoque entre 1 e 5 unidades, do menor estoque para o maior (desempate pelo nome).
**A2.** Produtos cujo nome termina com “GB” ou “TB” (sem diferenciar caixa).
**A3.** Quantos produtos há em cada faixa de preço: até 50, de 50 a 200, de 200 a 1000 e acima de 1000?
**A4.** Usuários cadastrados em 2026 cujo e-mail **não** termina em `@minishop.test`.

<details><summary>Soluções do bloco A</summary>

```sql
-- A1
SELECT sku, name, stock FROM products WHERE is_active AND stock BETWEEN 1 AND 5 ORDER BY stock, name;
-- A2
SELECT sku, name FROM products WHERE name ILIKE '%gb' OR name ILIKE '%tb' ORDER BY sku;
-- A3
SELECT CASE WHEN price <= 50 THEN '1) até 50' WHEN price <= 200 THEN '2) 50-200'
            WHEN price <= 1000 THEN '3) 200-1000' ELSE '4) acima de 1000' END AS faixa, count(*) AS produtos
FROM products GROUP BY 1 ORDER BY 1;
-- A4
SELECT id, email FROM users WHERE created_at >= '2026-01-01' AND created_at < '2027-01-01' AND email NOT LIKE '%@minishop.test' ORDER BY id;
```
```text
  sku  |          name           | stock 
-------+-------------------------+-------
 AU-02 | Fone com fio            |     1
 CB-05 | Cabo USB-C 2m           |     2
 PF-01 | Mouse sem fio           |     4
 AR-01 | SSD 240 GB              |     4
 MN-04 | Monitor 27 polegadas 4K |     5
(5 rows)

  sku  |         name          
-------+-----------------------
 AR-01 | SSD 240 GB
 AR-02 | SSD 480 GB
 AR-03 | SSD 1 TB
 AR-04 | SSD NVMe 1 TB
 AR-05 | HD externo 1 TB
 AR-06 | HD externo 2 TB
 AR-07 | Pen drive 64 GB
 AR-08 | Pen drive 128 GB
 AR-09 | Cartão microSD 128 GB
 PF-02 | Mouse gamer RGB
(10 rows)

      faixa       | produtos 
------------------+----------
 1) até 50        |       12
 2) 50-200        |       20
 3) 200-1000      |       14
 4) acima de 1000 |        4
(4 rows)

 id |       email        
----+--------------------
  1 | ana@exemplo.test
  2 | bruno@exemplo.test
  3 | carla@exemplo.test
  4 | diego@exemplo.test
  5 | elisa@exemplo.test
(5 rows)
```
</details>

### Bloco B: joins
**B1.** Os 5 maiores pedidos **pagos**: id, nome do cliente, nº de itens distintos e total.
**B2.** Itens do pedido 10, com nome do produto e da categoria.
**B3.** Valor vendido (pedidos pagos) por categoria, **incluindo** categorias sem vendas (zero).
**B4.** Pares (cliente, produto) comprados em **mais de um pedido pago** pelo mesmo cliente.

<details><summary>Soluções do bloco B</summary>

```sql
-- B1
SELECT o.id, u.name, count(oi.id) AS itens, o.total FROM orders o
JOIN users u ON u.id = o.user_id JOIN order_items oi ON oi.order_id = o.id
WHERE o.status = 'paid' GROUP BY o.id, u.name ORDER BY o.total DESC LIMIT 5;
-- B2
SELECT p.name, c.name AS categoria, oi.quantity, oi.unit_price FROM order_items oi
JOIN products p ON p.id = oi.product_id JOIN categories c ON c.id = p.category_id WHERE oi.order_id = 10 ORDER BY p.name;
-- B3
SELECT c.name, coalesce(sum(oi.quantity * oi.unit_price), 0) AS vendido
FROM categories c LEFT JOIN products p ON p.category_id = c.id
LEFT JOIN order_items oi ON oi.product_id = p.id LEFT JOIN orders o ON o.id = oi.order_id AND o.status = 'paid'
WHERE o.id IS NOT NULL OR oi.id IS NULL
GROUP BY c.id, c.name ORDER BY vendido DESC;
-- B4
SELECT u.name, p.name AS produto, count(DISTINCT o.id) AS pedidos FROM orders o
JOIN users u ON u.id = o.user_id JOIN order_items oi ON oi.order_id = o.id JOIN products p ON p.id = oi.product_id
WHERE o.status = 'paid' GROUP BY u.id, u.name, p.id, p.name HAVING count(DISTINCT o.id) > 1 ORDER BY pedidos DESC, u.name LIMIT 5;
```
```text
 id |     name     | itens |  total   
----+--------------+-------+----------
 10 | Diego Alves  |     3 | 10913.80
  7 | Diego Alves  |     4 |  7395.60
  5 | Bruno Lima   |     2 |  5639.85
 13 | Bruno Lima   |     4 |  4957.60
 12 | Carla Mendes |     3 |  1289.30
(5 rows)

           name           |   categoria   | quantity | unit_price 
--------------------------+---------------+----------+------------
 Monitor 27 polegadas 4K  | Monitores     |        3 |    2199.00
 Monitor 27 polegadas QHD | Monitores     |        3 |    1399.00
 Pen drive 128 GB         | Armazenamento |        2 |      59.90
(3 rows)

        name         | vendido  
---------------------+----------
 Monitores           | 27000.15
 Armazenamento       |  2148.40
 Áudio               |  1858.80
 Periféricos         |  1229.45
 Cabos e adaptadores |   629.08
(5 rows)

   name    |    produto    | pedidos 
-----------+---------------+---------
 Ana Souza | Cabo HDMI 2m  |       2
 Ana Souza | Cabo USB-C 1m |       2
(2 rows)
```
Na B3, o filtro `o.status = 'paid'` está no `ON`, mas, para somar só itens de pedidos pagos, é preciso descartar os itens de pedidos **não** pagos: a linha `WHERE o.id IS NOT NULL OR oi.id IS NULL` mantém as categorias sem nenhum item vendido e remove as linhas de pedidos pendentes/cancelados. Uma versão mais limpa usa uma subconsulta/CTE com os itens pagos e faz `LEFT JOIN` nela (tente reescrever).
</details>

### Bloco C: agregações
**C1.** Ticket médio e quantidade de pedidos por `status`.
**C2.** Meses em que o faturamento (pedidos pagos) superou R$ 5.000.
**C3.** Produtos com receita total acima de R$ 1.000 (`sum(quantity * unit_price)`), do maior para o menor.
**C4.** O cliente com mais pedidos cancelados, e quantos.

<details><summary>Soluções do bloco C</summary>

```sql
-- C1
SELECT status, count(*) AS pedidos, round(avg(total), 2) AS ticket_medio FROM orders GROUP BY status ORDER BY status;
-- C2
SELECT date_trunc('month', created_at)::date AS mes, sum(total) AS faturamento FROM orders
WHERE status = 'paid' GROUP BY 1 HAVING sum(total) > 5000 ORDER BY 1;
-- C3
SELECT p.sku, p.name, sum(oi.quantity * oi.unit_price) AS receita FROM order_items oi JOIN products p ON p.id = oi.product_id
GROUP BY p.id HAVING sum(oi.quantity * oi.unit_price) > 1000 ORDER BY receita DESC LIMIT 6;
-- C4
SELECT u.name, count(*) AS cancelados FROM orders o JOIN users u ON u.id = o.user_id WHERE o.status = 'cancelled'
GROUP BY u.id, u.name ORDER BY cancelados DESC, u.name LIMIT 1;
```
```text
  status   | pedidos | ticket_medio 
-----------+---------+--------------
 cancelled |       3 |      1178.21
 paid      |      12 |      2738.82
 pending   |       3 |       445.82
(3 rows)

    mes     | faturamento 
------------+-------------
 2026-04-01 |     5639.85
 2026-05-01 |     7550.10
 2026-06-01 |    11293.30
 2026-08-01 |     5356.80
(4 rows)

  sku  |            name            | receita  
-------+----------------------------+----------
 MN-04 | Monitor 27 polegadas 4K    | 13194.00
 MN-05 | Monitor curvo 32 polegadas | 11109.15
 MN-03 | Monitor 27 polegadas QHD   |  4197.00
 AR-04 | SSD NVMe 1 TB              |  1099.80
(4 rows)

    name     | cancelados 
-------------+------------
 Diego Alves |          2
(1 row)
```
</details>

### Bloco D: subqueries, CTEs e janelas
**D1.** Produtos cujo preço é o **maior da sua categoria**.
**D2.** Clientes que compraram algum produto da categoria “Monitores” em pedidos pagos.
**D3.** Para cada item de pedido, a diferença percentual entre o preço pago e o **preço atual** do produto; os 5 itens com maior desconto.
**D4.** Faturamento acumulado mês a mês (pedidos pagos).

<details><summary>Soluções do bloco D</summary>

```sql
-- D1
SELECT c.name AS categoria, p.sku, p.name, p.price FROM products p JOIN categories c ON c.id = p.category_id
WHERE p.price = (SELECT max(price) FROM products WHERE category_id = p.category_id) ORDER BY c.id;
-- D2
SELECT DISTINCT u.name FROM users u JOIN orders o ON o.user_id = u.id AND o.status = 'paid'
JOIN order_items oi ON oi.order_id = o.id JOIN products p ON p.id = oi.product_id
JOIN categories c ON c.id = p.category_id AND c.name = 'Monitores' ORDER BY u.name;
-- D3
SELECT oi.order_id, p.sku, oi.unit_price AS pago, p.price AS atual,
       round(100 * (oi.unit_price - p.price) / p.price, 1) AS dif_pct
FROM order_items oi JOIN products p ON p.id = oi.product_id ORDER BY dif_pct, oi.id LIMIT 5;
-- D4
SELECT mes, faturamento, sum(faturamento) OVER (ORDER BY mes) AS acumulado FROM (
  SELECT date_trunc('month', created_at)::date AS mes, sum(total) AS faturamento FROM orders WHERE status = 'paid' GROUP BY 1) m
ORDER BY mes LIMIT 5;
```
```text
      categoria      |  sku  |              name              |  price  
---------------------+-------+--------------------------------+---------
 Periféricos         | PF-03 | Teclado mecânico               |  329.00
 Áudio               | AU-09 | Soundbar                       |  449.90
 Monitores           | MN-10 | Monitor ultrawide 34 polegadas | 2899.00
 Cabos e adaptadores | CB-08 | Adaptador USB-C para HDMI      |   89.90
 Armazenamento       | AR-04 | SSD NVMe 1 TB                  |  549.90
 Armazenamento       | AR-06 | HD externo 2 TB                |  549.90
(6 rows)

    name     
-------------
 Bruno Lima
 Diego Alves
(2 rows)

 order_id |  sku  |  pago  | atual  | dif_pct 
----------+-------+--------+--------+---------
        1 | CB-09 |  33.16 |  34.90 |    -5.0
        2 | CB-09 |  33.16 |  34.90 |    -5.0
        3 | PF-03 | 312.55 | 329.00 |    -5.0
        3 | CB-08 |  85.40 |  89.90 |    -5.0
        4 | CB-09 |  33.16 |  34.90 |    -5.0
(5 rows)

    mes     | faturamento | acumulado 
------------+-------------+-----------
 2026-03-01 |      582.83 |    582.83
 2026-04-01 |     5639.85 |   6222.68
 2026-05-01 |     7550.10 |  13772.78
 2026-06-01 |    11293.30 |  25066.08
 2026-07-01 |     1289.30 |  26355.38
(5 rows)
```
</details>

### Bloco E: alteração de dados (sempre em transação!)
**E1.** Reduza em 10% o preço dos produtos **ativos sem nenhuma venda** e mostre quantos foram afetados; depois desfaça (`ROLLBACK`).
**E2.** Em um único comando, crie o usuário `fabio@exemplo.test`, o carrinho dele e 2 itens (use CTEs com `RETURNING`); depois desfaça.
**E3.** Tente apagar o usuário 2 (que tem pedidos), dentro de uma transação; observe a proteção da chave estrangeira e desfaça.

<details><summary>Soluções do bloco E</summary>

```sql
-- E1
BEGIN;
WITH alterados AS (
    UPDATE products SET price = round(price * 0.90, 2)
    WHERE is_active AND NOT EXISTS (SELECT 1 FROM order_items oi WHERE oi.product_id = products.id)
    RETURNING id
) SELECT count(*) AS produtos_alterados FROM alterados;
ROLLBACK;

-- E2
BEGIN;
WITH novo AS (INSERT INTO users (email, name) VALUES ('fabio@exemplo.test', 'Fábio Reis') RETURNING id),
     carrinho AS (INSERT INTO carts (user_id) SELECT id FROM novo RETURNING id)
INSERT INTO cart_items (cart_id, product_id, quantity) SELECT carrinho.id, p, q FROM carrinho, (VALUES (1, 2), (7, 1)) AS v(p, q)
RETURNING cart_id, product_id, quantity;
ROLLBACK;
```
```text
 produtos_alterados 
--------------------
                 18
(1 row)

 cart_id | product_id | quantity 
---------+------------+----------
       3 |          1 |        2
       3 |          7 |        1
(2 rows)
```
```sql
-- E3: o banco protege a integridade: o usuário 2 tem pedidos
BEGIN;
DELETE FROM users WHERE id = 2;
ROLLBACK;
```
```text
ERROR:  update or delete on table "users" violates foreign key constraint "orders_user_id_fkey" on table "orders"
DETAIL:  Key (id)=(2) is still referenced from table "orders".
```
Sem a chave estrangeira `orders.user_id → users.id`, o `DELETE` deixaria **pedidos órfãos**. A restrição existe para impedir isso (aula 08).
</details>

## 🧠 Pausa para lógica
**Problema (laço × conjunto).** Em Python, calcular o faturamento acumulado de uma lista de valores mensais exige um laço com acumulador. Escreva as duas versões (Python com `itertools.accumulate` e SQL com `sum() OVER`) e mostre que dão o mesmo resultado.

<details><summary>Dica</summary>
<code>itertools.accumulate(valores)</code> devolve as somas parciais; no SQL, <code>sum(x) OVER (ORDER BY mes)</code> faz o mesmo sobre a janela “do início até a linha atual”.
</details>

<details><summary>Solução comentada</summary>

```python
from itertools import accumulate
mensal = [582.83, 5639.85, 7550.10, 11293.30]
print([round(x, 2) for x in accumulate(mensal)])
```
```text
[582.83, 6222.68, 13772.78, 25066.08]
```
```sql
SELECT mes, round(sum(valor) OVER (ORDER BY mes), 2) AS acumulado
FROM (VALUES ('2026-03', 582.83), ('2026-04', 5639.85), ('2026-05', 7550.10), ('2026-06', 11293.30)) AS t(mes, valor);
```
```text
   mes   | acumulado 
---------+-----------
 2026-03 |    582.83
 2026-04 |   6222.68
 2026-05 |  13772.78
 2026-06 |  25066.08
(4 rows)
```
Mesma resposta, duas formas de pensar: o banco faz a operação em bloco sobre a tabela inteira, sem você traduzir cada linha para Python.
</details>

**Variação mais difícil:** média móvel de 3 meses (`ROWS BETWEEN 2 PRECEDING AND CURRENT ROW`).

## ⚠️ Erros comuns e boas práticas
| Erro | Sintoma | Solução |
|---|---|---|
| Granularidade errada | números duplicados ou agrupados demais | defina “uma linha do resultado é…” antes de escrever |
| Join que multiplica linhas | somas infladas | agregue antes de juntar ou confira com `count(*)` |
| Filtro de pedido pago no `WHERE` de um `LEFT JOIN` | categorias/clientes “somem” | condição no `ON` ou CTE |
| `NOT IN` com `NULL` | resultado vazio | `NOT EXISTS` |
| `UPDATE`/`DELETE` fora de transação | dados perdidos | `BEGIN` … conferir … `COMMIT`/`ROLLBACK` |
| Confiar na ordem sem `ORDER BY` | resultados diferentes a cada execução | sempre `ORDER BY` com desempate |

- Resolva **sem olhar** a solução, compare o resultado e só então leia como outra pessoa resolveu.
- Guarde cada consulta correta em um arquivo `.sql` versionado (vai virar documentação do projeto).
- Quando o resultado “parecer certo”, teste de outra forma (por exemplo, o total do relatório contra `sum(total)` direto).

## 🧩 Exercícios
**1. Fixação**
Refaça os 19 exercícios acima **sem consultar** as soluções. Marque na tabela abaixo quantos acertou de primeira.

| Bloco | Exercícios | Acertos de primeira |
|---|---|---|
| A | 4 | |
| B | 4 | |
| C | 4 | |
| D | 4 | |
| E | 3 | |

**2. Aplicação no projeto MiniShop**
Crie `projeto/sql/exercicios/respostas.sql` com as suas respostas e `projeto/sql/exercicios/novas.sql` com **5 perguntas de negócio suas**.

Critérios de pronto:
- [ ] As 19 consultas (A1 a E3) rodam sem erro no banco `loja` (`psql -f respostas.sql`)
- [ ] Cada consulta tem um comentário com a pergunta em português
- [ ] As 5 perguntas novas têm enunciado, consulta e uma linha dizendo como você validou o resultado
- [ ] As consultas de alteração estão em `BEGIN … ROLLBACK`
- [ ] Commit `feat(sql): add practice answers`

<details><summary>Sugestões de perguntas novas</summary>

Clientes que compraram em 3 meses seguidos; produtos que sempre são comprados juntos (pares no mesmo pedido); tempo médio entre o pedido e o pagamento (`payments.paid_at - orders.created_at`); produto mais caro vendido em cada mês; categorias em que mais de 50% dos produtos estão sem estoque.
</details>

**3. Desafio (opcional)**
“Produtos comprados juntos”: liste os pares de produtos que aparecem no mesmo pedido pelo menos 2 vezes (self join em `order_items`). É a base de recomendações (“quem comprou X também comprou Y”).

## 🎤 Na entrevista
- **Como você aborda uma consulta SQL complexa?** Defino a granularidade do resultado, identifico as tabelas e os joins, construo em camadas (CTEs), valido contagens e totais e testo casos de borda (sem dados, `NULL`).
- **Qual a diferença entre uma função agregada e uma função de janela?** A agregada colapsa as linhas de um grupo em uma só; a de janela calcula sobre um conjunto de linhas relacionado **sem** colapsá-las.
- **Como você altera dados em produção com segurança?** Primeiro um `SELECT` com o mesmo `WHERE`, dentro de uma transação, conferindo a contagem, e só então `COMMIT`; com backup e, se possível, em horário de baixo uso.

## 📚 Para ir além
- 📄 Documentação oficial: [Funções de janela (tutorial)](https://www.postgresql.org/docs/current/tutorial-window.html). Introdução a `OVER`, `PARTITION BY`, `rank`.
- 📄 Documentação oficial: [Consultas com `WITH`](https://www.postgresql.org/docs/current/queries-with.html). CTEs e `RETURNING` encadeado.
- 🎥 Vídeo (EN): *CS50 SQL* ([cs50.harvard.edu/sql](https://cs50.harvard.edu/sql/)), problemas de consulta com bancos reais.
- 🏋️ Prática extra: escolha um banco público pequeno (por exemplo, o de filmes do tutorial do SQLite/PostgreSQL), invente 10 perguntas e responda-as.

## ✅ Checklist da aula
- [ ] Resolvi os 19 exercícios (A1–E3) e registrei meus acertos
- [ ] Usei CTE, `EXISTS`, `HAVING` e uma função de janela
- [ ] Alterei dados apenas dentro de transação
- [ ] Entreguei `respostas.sql` e `novas.sql`
