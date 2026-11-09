# Cheatsheet: SQL (PostgreSQL)

## psql
`\l` bancos · `\c db` conectar · `\dt` tabelas · `\d tabela` estrutura · `\di` índices · `\x` expandido · `\timing` · `\i arq.sql` · `\q`

## Estrutura (DDL)
```sql
CREATE TABLE t (id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY, nome text NOT NULL UNIQUE,
                preco numeric(10,2) NOT NULL CHECK (preco >= 0), cat_id integer REFERENCES cats(id) ON DELETE RESTRICT,
                criado timestamptz NOT NULL DEFAULT now());
ALTER TABLE t ADD COLUMN x int; ALTER TABLE t DROP COLUMN x; DROP TABLE IF EXISTS t;
CREATE INDEX IF NOT EXISTS t_cat_idx ON t (cat_id);   CREATE INDEX ... WHERE cond;   CREATE INDEX ... ON t (lower(col));
```
## Dados (DML)
```sql
INSERT INTO t (a,b) VALUES (1,'x'),(2,'y') RETURNING id;
INSERT ... ON CONFLICT (col) DO NOTHING | DO UPDATE SET a = EXCLUDED.a;
UPDATE t SET a = a + 1 WHERE id = 1;   DELETE FROM t WHERE id = 1;   -- sempre com WHERE (teste em BEGIN/ROLLBACK)
```
## Consulta
```sql
SELECT DISTINCT c.nome, count(*) FILTER (WHERE p.ativo) AS n, sum(p.preco) AS total
FROM produtos p JOIN categorias c ON c.id = p.categoria_id
WHERE p.preco BETWEEN 10 AND 100 AND p.nome ILIKE '%mouse%'
GROUP BY c.id, c.nome HAVING count(*) > 2
ORDER BY total DESC NULLS LAST, c.id LIMIT 10 OFFSET 20;
```
| Ideia | Sintaxe |
|---|---|
| LEFT JOIN / sem par | `LEFT JOIN b ON ... WHERE b.id IS NULL` · `NOT EXISTS (SELECT 1 ...)` |
| Subquery / CTE | `WHERE x > (SELECT avg(x) FROM t)` · `WITH a AS (...) SELECT ...` |
| Janela | `sum(x) OVER (ORDER BY mes)` · `rank() OVER (PARTITION BY g ORDER BY v DESC)` · `lag(x) OVER (...)` |
| Conjuntos | `UNION [ALL]` · `INTERSECT` · `EXCEPT` |
| Condicional / nulo | `CASE WHEN ... THEN ... ELSE ... END` · `coalesce(x, 0)` · `nullif(x, 0)` · `IS DISTINCT FROM` |
| Datas | `date_trunc('month', ts)` · `ts >= now() - interval '30 days'` · `to_char(ts, 'DD/MM/YYYY')` |
| Keyset | `WHERE (preco, id) > (:p, :i) ORDER BY preco, id LIMIT 20` |

## Desempenho e transações
```sql
EXPLAIN (ANALYZE, BUFFERS) SELECT ...;     -- ANALYZE executa a consulta!
BEGIN; ... SAVEPOINT s; ... ROLLBACK TO s; COMMIT;
SELECT ... FOR UPDATE;     BEGIN ISOLATION LEVEL REPEATABLE READ;
UPDATE p SET stock = stock - :n WHERE id = :id AND stock >= :n;   -- confira o nº de linhas afetadas
```
## Python (psycopg 3)
```python
with psycopg.connect(DSN, row_factory=dict_row) as conn:      # COMMIT ao sair, ROLLBACK em erro, fecha
    conn.execute("SELECT * FROM p WHERE id = %s", (10,)).fetchone()       # NUNCA f-string com entrada de usuário
    with conn.transaction(): ...
```
## Backup
`pg_dump -Fc db > db.dump` · `pg_restore -d outro --no-owner < db.dump` · teste a restauração.
