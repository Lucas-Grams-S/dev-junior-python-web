# Checkpoint — Módulo 3: Bancos de dados relacionais

> ⏱️ ~1h30 · Faça **sem consultar** as aulas na primeira tentativa. 30 min para o quiz, 60 min para a entrega.

## 📝 Quiz (10 questões)
1. Cite quatro problemas de guardar os dados do MiniShop em um arquivo JSON que um banco relacional resolve.
2. Como se modela cada relacionamento (1:1, 1:N, N:N)? Dê um exemplo do MiniShop para cada.
3. Em `(pedido, produto, qtd, nome_produto, nome_cliente, cidade_cliente)` com chave `(pedido, produto)`, que formas normais são violadas e como corrigir? Quando faz sentido desnormalizar, e por que `order_items.unit_price` **não** é desnormalização?
4. Qual a ordem lógica de avaliação de um `SELECT`? Por que um alias do `SELECT` não funciona no `WHERE`?
5. Qual a diferença entre `INNER JOIN` e `LEFT JOIN`? Por que somar `orders.total` depois de juntar com `order_items` dá errado, e como achar produtos que nunca foram vendidos?
6. Explique `WHERE` × `HAVING` e `count(*)` × `count(coluna)` × `count(DISTINCT coluna)`.
7. O que é um índice e qual o custo? Por que `WHERE lower(email) = 'x'` ignora um índice em `email`? Como ler `Seq Scan` × `Index Scan` num `EXPLAIN ANALYZE`?
8. O que significa cada letra de ACID? Como evitar vender o mesmo item duas vezes (cite duas técnicas)? O que é um deadlock e como preveni-lo?
9. O que é SQL injection? Mostre o código vulnerável e o corrigido em `psycopg`, e diga como tratar um `ORDER BY` vindo do usuário.
10. O que é uma migração e por que **nunca** se edita uma já aplicada? Quando usar Redis, MongoDB e `jsonb`?

<details><summary>Gabarito</summary>

1. Concorrência (*lost update*), consultas lentas sem índice, ausência de integridade (FK, CHECK, UNIQUE), falta de durabilidade/atomicidade (arquivo corrompido a meio da gravação), consumo de memória/escala, e ausência de linguagem declarativa para relações (`JOIN`).
2. 1:1: FK com `UNIQUE` (usuário ↔ carrinho). 1:N: FK no lado “N” (categoria → produtos; usuário → pedidos). N:N: tabela de junção com duas FKs e atributos próprios (`order_items`, com `quantity` e `unit_price`).
3. `nome_produto` viola a 2FN (depende só de `produto`); `nome_cliente` e `cidade_cliente` dependem do pedido/cliente (2FN e, `cidade`, 3FN por dependência transitiva `pedido → cliente → cidade`). Corrigir com `produtos`, `clientes`, `pedidos(cliente_id)` e `itens(pedido_id, produto_id, qtd)`. Desnormalizar com consciência em totais/contadores/relatórios, com plano de consistência. `unit_price` é um **fato histórico** (o preço daquela compra), não uma cópia a sincronizar.
4. `FROM/JOIN` → `WHERE` → `GROUP BY` → `HAVING` → `SELECT` → `DISTINCT` → `ORDER BY` → `LIMIT/OFFSET`. O `WHERE` roda antes do `SELECT`, então o alias ainda não existe.
5. `INNER` só devolve pares; `LEFT` devolve todo o lado esquerdo, com `NULL` à direita se não houver par. O join 1:N repete o `total` do pedido em cada item, então a soma infla; some a coluna do lado “N” (`quantity * unit_price`) ou agregue antes. Nunca vendidos: `LEFT JOIN ... WHERE oi.id IS NULL` ou `NOT EXISTS`.
6. `WHERE` filtra linhas antes de agrupar; `HAVING` filtra grupos depois (aceita agregados). `count(*)` conta linhas; `count(col)` ignora `NULL`; `count(DISTINCT col)` conta valores distintos não nulos.
7. Estrutura auxiliar (B-tree) que acelera busca por valor/faixa/ordem, ao custo de espaço e de escritas mais lentas. A função altera o valor comparado e o índice guarda o valor bruto (solução: índice de expressão `lower(email)`). `Seq Scan` lê a tabela toda; `Index/Bitmap Index Scan` usa o índice; compare linhas estimadas × reais, `Rows Removed by Filter`, `Buffers` e `Execution Time`.
8. Atomicidade (tudo ou nada), Consistência (respeita as regras), Isolamento (transações concorrentes não se interferem), Durabilidade (confirmado não se perde). Venda dupla: `UPDATE ... SET stock = stock - n WHERE stock >= n` conferindo as linhas afetadas, ou `SELECT ... FOR UPDATE` (mais `CHECK (stock >= 0)`). Deadlock: duas transações esperando uma pela outra; prevenir com ordem fixa de travas, transações curtas e retentativa.
9. Concatenar entrada do usuário ao SQL, alterando sua estrutura. Vulnerável: `conn.execute(f"... name ILIKE '%{termo}%'")`. Correto: `conn.execute("... name ILIKE %s", (f"%{termo}%",))`. `ORDER BY`: lista de permissão (`dict` de entrada → coluna) e `sql.Identifier`; nunca repassar o texto.
10. Arquivo versionado e ordenado que descreve uma mudança de schema, registrada em uma tabela de controle. Não se edita porque outros ambientes já a aplicaram, e editar cria bancos diferentes sem registro; crie outra. Redis: cache, contadores, sessões, filas; MongoDB: documentos autocontidos de esquema muito variável; `jsonb`: atributos variáveis dentro do PostgreSQL, que continua sendo a fonte da verdade.
</details>

## 🛠️ Entrega prática
Repositório `minishop` na tag `v0.3-banco-sql`, com `projeto/sql/`:
- [ ] `01_schema.sql`, `02_seed.sql` (≥ 20 produtos, ≥ 3 usuários, ≥ 8 pedidos coerentes), `03_indices.sql`, `04_views.sql`, `05_funcoes.sql`
- [ ] `verify.sql` com ≥ 8 verificações; `run_all.sh` recria o banco do zero e termina em `OK`
- [ ] `consultas/` (`catalogo.sql`, `pedidos.sql`, `relatorios.sql`) e `exercicios/` (`respostas.sql`, `novas.sql`) rodando sem erro
- [ ] `indices.sql`/`docs/desempenho-sql.md` com `EXPLAIN ANALYZE` antes/depois de 3 consultas
- [ ] `transacoes/criar_pedido.sql` e a função `fn_create_order` (pedido atômico, estoque condicional)
- [ ] `docs/modelo-er.md` (diagrama Mermaid) e `docs/banco.md` (como recriar, backup **testado**, decisões)
- [ ] Pacote `minishop_db/` (psycopg) **sem** SQL concatenado (`grep -rn 'execute(f' minishop_db` vazio), com testes pytest, inclusive de injeção
- [ ] `migrar.py` e `projeto/sql/migracoes/` aplicando o schema do zero em um banco vazio
- [ ] Tag publicada: `git tag v0.3-banco-sql && git push --tags`

**Prova de fogo (40 min, sem consultar):** (1) escreva a consulta “top 3 clientes por valor pago em 2026, com a participação % no total”; (2) crie um índice que acelere “pedidos de um usuário nos últimos 30 dias, mais recentes primeiro” e mostre o `EXPLAIN` antes e depois; (3) explique por que `SELECT ... WHERE name = '$x'` montado com f-string é inaceitável e reescreva com `psycopg`.

## 🪞 Autoavaliação
Nota de 0 a 3. Se algum item ficar em **0 ou 1**, refaça a aula antes de seguir.

| Habilidade | Aula | Nota |
|---|---|---|
| Justificar o banco e desenhar um ER | 01 | |
| Normalizar até a 3FN e decidir desnormalizar | 02 | |
| Subir o PostgreSQL e usar DDL/DML/`psql` | 03 | |
| Filtrar, ordenar e paginar (inclusive keyset) | 04 | |
| Escolher e escrever JOINs, anti-join | 05 | |
| Agregar, `HAVING`, subqueries, CTEs | 06 | |
| Resolver problemas de negócio em SQL | 07 | |
| Constraints, índices e ler `EXPLAIN` | 08 | |
| Transações, ACID, isolamento, travas | 09 | |
| `psycopg` e prevenção de SQL injection | 10 | |
| ORM, migrações e escolher Redis/Mongo/`jsonb` | 11 | |
| Reconstruir, verificar e fazer backup do banco | 12 | |

## 🧠 Lógica: lista de verificação
Resolveu sem olhar: junção por hash à mão (01), dependência funcional `A → B` (02), seed idempotente (03), paginação por `OFFSET` e por cursor (04), `left_join` em Python (05), ranking SQL × `Counter` (06), acumulado com `accumulate` e `sum() OVER` (07), altura de uma B-tree (08), transação como *context manager* (09), filtros dinâmicos sem concatenação (10), cache com TTL (11), ordenação topológica das tabelas (12)? Marque o que faltou e refaça.

➡️ Próximo: [Módulo 4 — Front-end essencial para dev backend](../04-front-end-essencial/README.md).
