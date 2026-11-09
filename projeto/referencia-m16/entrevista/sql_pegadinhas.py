"""Pegadinhas de banco para entrevista (aula 16.04). SQLite em memória; cada bloco imprime o resultado REAL."""

import sqlite3

c = sqlite3.connect(":memory:")
c.executescript(
    """
CREATE TABLE clientes (id INTEGER PRIMARY KEY, nome TEXT);
CREATE TABLE pedidos (id INTEGER PRIMARY KEY, cliente_id INTEGER, total INTEGER, status TEXT);
INSERT INTO clientes VALUES (1,'Ana'),(2,'Bruno'),(3,'Carla');
INSERT INTO pedidos VALUES (1,1,100,'pago'),(2,1,50,'pago'),(3,2,70,'cancelado'),(4,NULL,30,'pago');
"""
)


def q(titulo: str, sql: str) -> None:
    print(f"-- {titulo}\n   {' '.join(sql.split())}\n   -> {c.execute(sql).fetchall()}")


q(
    "1) INNER JOIN: Carla some",
    "SELECT c.nome, p.total FROM clientes c JOIN pedidos p ON p.cliente_id=c.id ORDER BY 1,2",
)
q(
    "2) LEFT JOIN: Carla aparece com NULL",
    "SELECT c.nome, p.total FROM clientes c LEFT JOIN pedidos p ON p.cliente_id=c.id ORDER BY 1,2",
)
q(
    "3) LEFT JOIN + WHERE no lado direito vira INNER (Carla some de novo)",
    "SELECT c.nome FROM clientes c LEFT JOIN pedidos p ON p.cliente_id=c.id WHERE p.status='pago' ORDER BY 1",
)
q(
    "4) mesmo filtro no ON preserva Carla",
    "SELECT c.nome, p.total FROM clientes c LEFT JOIN pedidos p ON p.cliente_id=c.id AND p.status='pago' ORDER BY 1,2",
)
q(
    "5) NULL: = NULL não casa; IS NULL casa",
    "SELECT (SELECT count(*) FROM pedidos WHERE cliente_id = NULL), (SELECT count(*) FROM pedidos WHERE cliente_id IS NULL)",
)
q(
    "6) NOT IN com NULL na subconsulta devolve vazio",
    "SELECT nome FROM clientes WHERE id NOT IN (SELECT cliente_id FROM pedidos)",
)
q(
    "7) NOT EXISTS é o jeito seguro",
    "SELECT nome FROM clientes c WHERE NOT EXISTS (SELECT 1 FROM pedidos p WHERE p.cliente_id=c.id) ORDER BY 1",
)
q("8) COUNT(*) × COUNT(coluna)", "SELECT count(*), count(cliente_id) FROM pedidos")
q(
    "9) WHERE × HAVING",
    "SELECT cliente_id, sum(total) s FROM pedidos WHERE status='pago' GROUP BY cliente_id HAVING s > 40 ORDER BY 1",
)

# índice: o plano muda de SCAN para SEARCH
plano = lambda: [r[3] for r in c.execute("EXPLAIN QUERY PLAN SELECT * FROM pedidos WHERE cliente_id = 1")]
print("-- 10) sem índice:", plano())
c.execute("CREATE INDEX pedidos_cliente ON pedidos(cliente_id)")
print("   com índice:", plano())

# transação: tudo ou nada
c.execute("CREATE TABLE contas (id INTEGER PRIMARY KEY, saldo INTEGER CHECK (saldo >= 0))")
c.execute("INSERT INTO contas VALUES (1,100),(2,0)")
c.commit()
try:
    with c:  # commit se sair bem, rollback se levantar exceção
        c.execute("UPDATE contas SET saldo = saldo + 150 WHERE id = 2")
        c.execute("UPDATE contas SET saldo = saldo - 150 WHERE id = 1")  # viola o CHECK
except sqlite3.IntegrityError as e:
    print("-- 11) transação desfeita:", e, "| saldos:", c.execute("SELECT * FROM contas").fetchall())
