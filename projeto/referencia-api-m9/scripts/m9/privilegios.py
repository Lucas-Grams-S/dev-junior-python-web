"""O que cada papel do banco consegue (e não consegue) fazer. Conexões reais ao PostgreSQL 18 do laboratório."""
import psycopg

BASE = "host=127.0.0.1 port=5498 dbname=minishop_m9"
PAPEIS = {"minishop_app": "app-lab-apenas", "minishop_ro": "ro-lab-apenas"}
TESTES = [
    ("SELECT count(*) FROM catalog_product", "ler produtos"),
    ("UPDATE catalog_product SET stock = stock WHERE id = 1", "atualizar um produto"),
    ("INSERT INTO catalog_category (name, slug) VALUES ('Teste', 'teste-' || floor(random()*1e6)::int)", "inserir categoria"),
    ("DELETE FROM catalog_category WHERE slug LIKE 'teste-%'", "apagar a categoria de teste"),
    ("ALTER TABLE catalog_product ADD COLUMN espiao text", "ALTERAR a estrutura da tabela"),
    ("DROP TABLE catalog_product CASCADE", "APAGAR a tabela de produtos"),
    ("TRUNCATE catalog_product CASCADE", "ESVAZIAR a tabela de produtos"),
    ("CREATE TABLE backdoor (x int)", "CRIAR uma tabela nova"),
    ("CREATE ROLE intruso LOGIN", "criar um papel"),
]
print(f"{'papel':<13} {'operação':<34} resultado")
for papel, senha in PAPEIS.items():
    for sql, descricao in TESTES:
        with psycopg.connect(f"{BASE} user={papel} password={senha}", autocommit=True) as c:
            try:
                cur = c.execute(sql)
                resultado = "permitido" + (f" (retornou {cur.fetchone()[0]})" if sql.startswith("SELECT") else "")
            except psycopg.errors.InsufficientPrivilege as e:
                resultado = "NEGADO  → " + str(e).splitlines()[0][:62]
            except psycopg.Error as e:
                resultado = f"erro ({e.__class__.__name__})"
        print(f"{papel:<13} {descricao:<34} {resultado}")
    print()
