# 06. GROUP BY, HAVING e subqueries

> ⏱️ ~1h30 · Módulo 3 · Pré-requisitos: [05](05-joins.md)

## 🎯 Objetivos
Ao final desta aula você consegue:
- Calcular agregações (`count`, `sum`, `avg`, `min`, `max`) com e sem `GROUP BY`
- Filtrar grupos com `HAVING` e linhas com `WHERE`, sabendo a diferença
- Usar subconsultas escalares, em `IN`, `EXISTS`, correlacionadas e em `FROM`
- Organizar consultas complexas com CTEs (`WITH`)
- Combinar resultados com `UNION`, `INTERSECT` e `EXCEPT`

## 🤔 Por que isso importa
Painéis, relatórios e rankings (“mais vendidos”, “faturamento por mês”, “clientes que mais compram”) são agregações. É o que o ORM chama de `annotate()`/`aggregate()` (aula 5.6). Quem domina `GROUP BY` constrói em minutos o que levaria um laço em Python com milhares de linhas puxadas do banco.

## 💡 Intuição (explicação simples)
`GROUP BY` é **separar os recibos em pilhas** (uma pilha por cliente, por mês…) e **resumir cada pilha** com uma única linha (quantos, quanto somam, qual o maior). `HAVING` é “**fique só com as pilhas que...**” (as que somam mais de mil). Uma subquery é uma **pergunta dentro da pergunta**: “os produtos mais caros que *a média da sua categoria*”.

## 🔬 Como funciona por dentro
- Uma função **agregada** reduz várias linhas a um valor. Sem `GROUP BY`, o resultado inteiro é **um grupo só**.
- Com `GROUP BY`, cada coluna do `SELECT` precisa estar **no `GROUP BY` ou dentro de um agregado** (senão o banco não saberia qual valor mostrar da pilha).
- Ordem lógica (aula 04): `FROM/JOIN` → `WHERE` (filtra linhas) → `GROUP BY` → `HAVING` (filtra grupos) → `SELECT` → `ORDER BY` → `LIMIT`.
- **`count(*)`** conta linhas; **`count(coluna)`** ignora `NULL`; **`count(DISTINCT coluna)`** conta valores distintos. `sum`/`avg` ignoram `NULL` (e `sum` de nada é `NULL`: use `coalesce`).
- **Subconsulta correlacionada** referencia a linha da consulta externa e é reavaliada por linha (o planejador costuma transformá-la em join).
- **CTE** (`WITH nome AS (...)`) dá nome a um passo intermediário e torna consultas longas legíveis.

| Subquery | Onde | Devolve |
|---|---|---|
| escalar | `SELECT`, `WHERE` | 1 linha, 1 coluna |
| lista | `IN (SELECT ...)` | 1 coluna, N linhas |
| existência | `EXISTS (SELECT 1 ...)` | verdadeiro/falso |
| tabela derivada | `FROM (SELECT ...) AS t` | uma tabela temporária |

## 🛠️ Exemplo prático
Banco `loja`. Saídas reais.

**1. Agregações sem `GROUP BY`**
```sql
SELECT count(*) AS produtos,
       count(*) FILTER (WHERE is_active) AS ativos,
       min(price) AS mais_barato, max(price) AS mais_caro,
       round(avg(price), 2) AS media, sum(stock) AS unidades
FROM products;
```
```text
 produtos | ativos | mais_barato | mais_caro | media  | unidades 
----------+--------+-------------+-----------+--------+----------
       50 |     47 |       24.90 |   2899.00 | 355.92 |      945
(1 row)
```
`FILTER (WHERE ...)` aplica a condição só àquela agregação (mais legível que `CASE` dentro do `sum`).

**2. `GROUP BY`: uma linha por grupo**
```sql
SELECT c.name AS categoria, count(*) AS produtos, round(avg(p.price), 2) AS preco_medio,
       sum(p.stock) AS unidades, max(p.price) AS mais_caro
FROM products p JOIN categories c ON c.id = p.category_id
GROUP BY c.id, c.name
ORDER BY preco_medio DESC;
```
```text
      categoria      | produtos | preco_medio | unidades | mais_caro 
---------------------+----------+-------------+----------+-----------
 Monitores           |       10 |     1137.27 |      235 |   2899.00
 Armazenamento       |       10 |      261.90 |      195 |    549.90
 Áudio               |       10 |      197.90 |      172 |    449.90
 Periféricos         |       10 |      137.81 |      163 |    329.00
 Cabos e adaptadores |       10 |       44.70 |      180 |     89.90
(5 rows)
```
**3. `HAVING` × `WHERE`**
```sql
-- WHERE filtra LINHAS antes de agrupar; HAVING filtra GRUPOS depois
SELECT user_id, count(*) AS pedidos_pagos, sum(total) AS gasto
FROM orders
WHERE status = 'paid'
GROUP BY user_id
HAVING sum(total) > 3000
ORDER BY gasto DESC;
```
```text
 user_id | pedidos_pagos |  gasto   
---------+---------------+----------
       4 |             2 | 18309.40
       2 |             5 | 12234.50
(2 rows)
```
**4. Agrupar por expressão (mês) e por vários campos**
```sql
SELECT date_trunc('month', created_at)::date AS mes, status, count(*) AS pedidos, sum(total) AS valor
FROM orders
GROUP BY 1, 2
ORDER BY 1, 2
LIMIT 8;
```
```text
    mes     |  status   | pedidos |  valor   
------------+-----------+---------+----------
 2026-02-01 | pending   |       1 |    33.16
 2026-03-01 | cancelled |       1 |    66.32
 2026-03-01 | paid      |       2 |   582.83
 2026-04-01 | paid      |       1 |  5639.85
 2026-05-01 | paid      |       2 |  7550.10
 2026-06-01 | paid      |       2 | 11293.30
 2026-06-01 | pending   |       1 |   404.50
 2026-07-01 | cancelled |       1 |   899.80
(8 rows)
```
`GROUP BY 1, 2` usa a posição das colunas do `SELECT` (útil, mas prefira nomes em consultas longas).

**5. `string_agg` e `array_agg`: juntar valores do grupo**
```sql
SELECT o.id, string_agg(p.sku, ', ' ORDER BY p.sku) AS itens, sum(oi.quantity) AS unidades
FROM orders o JOIN order_items oi ON oi.order_id = o.id JOIN products p ON p.id = oi.product_id
GROUP BY o.id ORDER BY o.id LIMIT 4;
```
```text
 id |    itens     | unidades 
----+--------------+----------
  1 | CB-09        |        1
  2 | CB-09        |        3
  3 | CB-08, PF-03 |        3
  4 | CB-09        |        2
(4 rows)
```
**6. Erro clássico do `GROUP BY`**
```sql
SELECT c.name, p.name, count(*) FROM products p JOIN categories c ON c.id = p.category_id GROUP BY c.name;
```
```text
ERROR:  column "p.name" must appear in the GROUP BY clause or be used in an aggregate function
LINE 1: SELECT c.name, p.name, count(*) FROM products p JOIN categor...
                       ^
```
`p.name` não está no `GROUP BY` nem em agregado: dentro de cada categoria existem 10 nomes de produto; o banco se recusa a escolher um.

**7. Subconsultas**
```sql
-- escalar: produtos mais caros que a média geral
SELECT sku, name, price FROM products
WHERE price > (SELECT avg(price) FROM products) ORDER BY price DESC LIMIT 3;

-- lista (IN): produtos da categoria de nome 'Monitores'
SELECT count(*) AS monitores FROM products WHERE category_id IN (SELECT id FROM categories WHERE name = 'Monitores');

-- existência (EXISTS): clientes que já tiveram um pedido pago
SELECT u.name FROM users u
WHERE EXISTS (SELECT 1 FROM orders o WHERE o.user_id = u.id AND o.status = 'paid') ORDER BY u.id;
```
```text
  sku  |              name              |  price  
-------+--------------------------------+---------
 MN-10 | Monitor ultrawide 34 polegadas | 2899.00
 MN-04 | Monitor 27 polegadas 4K        | 2199.00
 MN-05 | Monitor curvo 32 polegadas     | 1899.00
(3 rows)

 monitores 
-----------
        10
(1 row)

     name     
--------------
 Ana Souza
 Bruno Lima
 Carla Mendes
 Diego Alves
(4 rows)
```
**8. Correlacionada: acima da média *da própria categoria***
```sql
SELECT p.sku, p.name, p.price, c.name AS categoria
FROM products p JOIN categories c ON c.id = p.category_id
WHERE p.price > (SELECT avg(p2.price) FROM products p2 WHERE p2.category_id = p.category_id)
ORDER BY c.id, p.price DESC
LIMIT 6;
```
```text
  sku  |       name       | price  |  categoria  
-------+------------------+--------+-------------
 PF-03 | Teclado mecânico | 329.00 | Periféricos
 PF-05 | Webcam Full HD   | 219.90 | Periféricos
 PF-02 | Mouse gamer RGB  | 159.90 | Periféricos
 PF-04 | Teclado compacto | 149.90 | Periféricos
 AU-09 | Soundbar         | 449.90 | Áudio
 AU-06 | Microfone USB    | 349.90 | Áudio
(6 rows)
```
O `p.category_id` dentro da subquery vem da linha externa: a média é recalculada para a categoria de cada produto.

**9. Tabela derivada e CTE: faturamento mensal e variação**
```sql
WITH mensal AS (
    SELECT date_trunc('month', created_at)::date AS mes, sum(total) AS faturamento
    FROM orders WHERE status = 'paid' GROUP BY 1
),
com_anterior AS (
    SELECT mes, faturamento, lag(faturamento) OVER (ORDER BY mes) AS mes_anterior FROM mensal
)
SELECT mes, faturamento, mes_anterior,
       round(100.0 * (faturamento - mes_anterior) / mes_anterior, 1) AS variacao_pct
FROM com_anterior ORDER BY mes LIMIT 6;
```
```text
    mes     | faturamento | mes_anterior | variacao_pct 
------------+-------------+--------------+--------------
 2026-03-01 |      582.83 |              |             
 2026-04-01 |     5639.85 |       582.83 |        867.7
 2026-05-01 |     7550.10 |      5639.85 |         33.9
 2026-06-01 |    11293.30 |      7550.10 |         49.6
 2026-07-01 |     1289.30 |     11293.30 |        -88.6
 2026-08-01 |     5356.80 |      1289.30 |        315.5
(6 rows)
```
`lag(...) OVER (ORDER BY ...)` é uma **função de janela**: olha para a linha anterior sem colapsar as linhas (diferente do `GROUP BY`). Funções de janela (`row_number`, `rank`, `lag`, `sum() OVER`) são ótimas para rankings e comparações; veja a documentação.

**10. Conjuntos: `UNION`, `INTERSECT`, `EXCEPT`**
```sql
SELECT user_id FROM orders WHERE status = 'paid'
INTERSECT SELECT user_id FROM orders WHERE status = 'cancelled' ORDER BY 1;   -- compraram E cancelaram

SELECT id FROM users EXCEPT SELECT user_id FROM orders ORDER BY 1;            -- nunca pediram

SELECT 'produto' AS tipo, sku AS codigo FROM products WHERE stock = 0
UNION ALL SELECT 'categoria', slug FROM categories WHERE id = 1;              -- UNION ALL mantém duplicatas (mais rápido)
```
```text
 user_id 
---------
       2
       4
(2 rows)

 id 
----
  5
  6
(2 rows)

   tipo    |   codigo    
-----------+-------------
 produto   | PF-05
 produto   | AU-08
 produto   | CB-04
 categoria | perifericos
(4 rows)
```
## ⚠️ Erros comuns e boas práticas
| Mensagem / sintoma | Causa | Solução |
|---|---|---|
| `ERROR: column "p.name" must appear in the GROUP BY clause or be used in an aggregate function` | Coluna solta no `SELECT` | Agrupe por ela ou agregue |
| `ERROR: aggregate functions are not allowed in WHERE` | `WHERE sum(x) > 10` | Use `HAVING` |
| `ERROR: more than one row returned by a subquery used as an expression` | Subquery escalar devolveu várias linhas | `LIMIT 1`, agregue ou use `IN` |
| Média “errada” | `avg` ignora `NULL`; join multiplicou linhas | Confira os `NULL`s e o número de linhas do join |
| `count(*)` dá 1 para quem não tem pedidos (em `LEFT JOIN`) | contou a linha-fantasma | `count(o.id)` |
| `sum()` devolve `NULL` | grupo sem linhas | `coalesce(sum(x), 0)` |
| `division by zero` | divisor `0` | `nullif(divisor, 0)` |

- Em relatórios, **agregue no banco**, não em Python: trazer 100 mil linhas para somar é lento e caro.
- Prefira CTEs nomeadas a subconsultas aninhadas em 3 níveis.
- Confira o resultado com um caso pequeno calculado à mão.
- `UNION` remove duplicatas (ordena/compara tudo); se não precisa disso, use `UNION ALL`.

## 🧠 Pausa para lógica
**Problema (ranking de mais vendidos).** Calcule os 5 produtos mais vendidos (soma de `quantity`) em SQL e **confirme** com um `Counter` em Python alimentado pelos mesmos dados. Por que o desempate precisa ser definido?

<details><summary>Dica</summary>
Em SQL, <code>GROUP BY product_id ORDER BY sum(quantity) DESC, product_id</code>. Em Python, <code>Counter</code> somando <code>quantity</code> por <code>product_id</code> e <code>most_common</code> (o desempate do <code>Counter</code> segue a ordem de inserção; ordene explicitamente).
</details>

<details><summary>Solução comentada</summary>

```bash
Q="SELECT product_id, sum(quantity) AS n FROM order_items GROUP BY product_id ORDER BY n DESC, product_id LIMIT 5"
echo "# SQL:"; docker exec minishop-pg psql -U postgres -d loja -X -t -A -F ' ' -c "$Q"
echo "# Python (Counter):"
docker exec minishop-pg psql -U postgres -d loja -X -t -A -F ',' -c "SELECT product_id, quantity FROM order_items" | python -c "
import sys
from collections import Counter
c = Counter()
for linha in sys.stdin:
    pid, qtd = linha.strip().split(',')
    c[int(pid)] += int(qtd)
top = sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))[:5]     # desempate explícito pelo id
for pid, n in top: print(pid, n)
"
```
```text
# SQL:
34 8
39 8
24 6
25 6
47 5
# Python (Counter):
34 8
39 8
24 6
25 6
47 5
```
As duas listas coincidem. Se houver empate na 5ª posição, sem o desempate (`product_id`) o resultado poderia variar entre execuções. O banco faz a soma sem trazer as 44 linhas ao Python (com 44 milhões, essa diferença seria a de segundos contra horas).
</details>

**Variação mais difícil:** ranking **por categoria** (os 2 mais vendidos de cada uma), com `row_number() OVER (PARTITION BY ... ORDER BY ...)`.

## 🧩 Exercícios
**1. Fixação**
(a) Valor total de pedidos pagos por usuário, só de quem gastou mais que a média dos pagantes; (b) categorias com mais de 10 produtos ativos (esperado: nenhuma, por quê?); (c) produtos que aparecem em pelo menos 3 pedidos diferentes; (d) o pedido de maior valor de cada usuário.

<details><summary>Solução</summary>

```sql
WITH gasto AS (SELECT user_id, sum(total) AS g FROM orders WHERE status = 'paid' GROUP BY user_id)
SELECT user_id, g FROM gasto WHERE g > (SELECT avg(g) FROM gasto) ORDER BY g DESC;

SELECT category_id, count(*) FROM products WHERE is_active GROUP BY category_id HAVING count(*) > 10;

SELECT product_id, count(DISTINCT order_id) AS pedidos FROM order_items GROUP BY product_id HAVING count(DISTINCT order_id) >= 3 ORDER BY pedidos DESC, product_id LIMIT 5;

SELECT DISTINCT ON (user_id) user_id, id AS pedido, total FROM orders ORDER BY user_id, total DESC;
```
```text
 user_id |    g     
---------+----------
       4 | 18309.40
       2 | 12234.50
(2 rows)

 category_id | count 
-------------+-------
(0 rows)

 product_id | pedidos 
------------+---------
         39 |       4
         24 |       3
         34 |       3
(3 rows)

 user_id | pedido |  total   
---------+--------+----------
       1 |     16 |   899.80
       2 |      5 |  5639.85
       3 |     12 |  1289.30
       4 |     10 | 10913.80
(4 rows)
```
(b) Cada categoria tem 10 produtos no total (e algumas têm menos ativos), então nenhuma passa de 10. O `DISTINCT ON` é um recurso do PostgreSQL para “o primeiro de cada grupo”.
</details>

**2. Aplicação no projeto MiniShop**
Escreva `projeto/sql/consultas/relatorios.sql` com os relatórios do painel administrativo.

Critérios de pronto:
- [ ] (1) Faturamento por mês (apenas pedidos `paid`) com a variação % sobre o mês anterior
- [ ] (2) Ticket médio e número de pedidos por cliente
- [ ] (3) Top 5 produtos por unidades vendidas e top 5 por receita (`sum(quantity * unit_price)`)
- [ ] (4) Estoque por categoria (unidades e valor), destacando categorias com mais de 10% de produtos esgotados
- [ ] (5) Taxa de conversão: pedidos pagos ÷ pedidos criados, por mês
- [ ] Cada relatório em uma CTE legível, comentado, sem erro de divisão por zero (`nullif`)
- [ ] Commit `feat(sql): add admin reports`

<details><summary>Solução de referência</summary>

```sql
-- (3) top por receita
SELECT p.sku, p.name, sum(oi.quantity) AS unidades, sum(oi.quantity * oi.unit_price) AS receita
FROM order_items oi JOIN products p ON p.id = oi.product_id JOIN orders o ON o.id = oi.order_id AND o.status = 'paid'
GROUP BY p.id ORDER BY receita DESC LIMIT 5;
-- (5) conversão mensal
SELECT date_trunc('month', created_at)::date AS mes, count(*) AS criados,
       count(*) FILTER (WHERE status = 'paid') AS pagos,
       round(100.0 * count(*) FILTER (WHERE status = 'paid') / nullif(count(*), 0), 1) AS conversao_pct
FROM orders GROUP BY 1 ORDER BY 1 LIMIT 4;
```
```text
  sku  |            name            | unidades | receita  
-------+----------------------------+----------+----------
 MN-05 | Monitor curvo 32 polegadas |        6 | 11109.15
 MN-04 | Monitor 27 polegadas 4K    |        5 | 10995.00
 MN-03 | Monitor 27 polegadas QHD   |        3 |  4197.00
 AR-04 | SSD NVMe 1 TB              |        2 |  1099.80
 AU-03 | Headset gamer              |        3 |   899.70
(5 rows)

    mes     | criados | pagos | conversao_pct 
------------+---------+-------+---------------
 2026-02-01 |       1 |     0 |           0.0
 2026-03-01 |       3 |     2 |          66.7
 2026-04-01 |       1 |     1 |         100.0
 2026-05-01 |       2 |     2 |         100.0
(4 rows)
```
</details>

**3. Desafio (opcional)**
Calcule a **curva ABC**: ordene os produtos por receita e marque como “A” os que somam os primeiros 80% do faturamento (`sum() OVER (ORDER BY ...)`).

## 🎤 Na entrevista
- **Qual a diferença entre `WHERE` e `HAVING`?** `WHERE` filtra linhas antes da agregação; `HAVING` filtra grupos depois (pode usar agregados).
- **O que faz `GROUP BY` e por que toda coluna do `SELECT` precisa estar nele ou em um agregado?** Agrupa linhas com mesmo valor; sem agregar, o banco não saberia qual valor do grupo exibir.
- **`count(*)` vs `count(coluna)` vs `count(DISTINCT coluna)`?** Todas as linhas; as não nulas; os valores distintos não nulos.
- **Subquery correlacionada: o que é e qual o custo?** Subconsulta que usa colunas da externa e é avaliada por linha; pode ser cara, e muitas vezes se reescreve como `JOIN` ou CTE.

## 📚 Para ir além
- 📄 Documentação oficial: [Tutorial de agregação (PostgreSQL)](https://www.postgresql.org/docs/current/tutorial-agg.html). `GROUP BY`/`HAVING` com exemplos.
- 📄 Documentação oficial: [Funções agregadas](https://www.postgresql.org/docs/current/functions-aggregate.html). Lista completa (`FILTER`, `string_agg`…).
- 📄 Documentação oficial: [CTEs (`WITH`)](https://www.postgresql.org/docs/current/queries-with.html). Consultas com nome e recursivas.
- 🎥 Vídeo (EN): *CS50 SQL* ([cs50.harvard.edu/sql](https://cs50.harvard.edu/sql/)), semanas de agregação e subconsultas.
- 🏋️ Prática extra: monte o relatório “clientes por faixa de gasto” (0, até 1000, até 5000, mais) com `CASE` e `GROUP BY`.

## ✅ Checklist da aula
- [ ] Provoquei o erro de `GROUP BY` e o corrigi
- [ ] Usei `HAVING`, `FILTER`, `EXISTS` e uma CTE
- [ ] Conferi um ranking SQL com `Counter`
- [ ] Entreguei `relatorios.sql`
