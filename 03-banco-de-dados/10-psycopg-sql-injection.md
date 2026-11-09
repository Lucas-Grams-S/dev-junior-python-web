# 10. Python + PostgreSQL com `psycopg` e SQL injection

> ⏱️ ~1h30 · Módulo 3 · Pré-requisitos: [03](03-postgres-docker-ddl-dml.md), [09](09-transacoes-acid.md); *context managers* da [aula 1.16](../01-python-logica/16-decorators-context-managers.md)

## 🎯 Objetivos
Ao final desta aula você consegue:
- Conectar ao PostgreSQL com `psycopg` 3 e executar consultas parametrizadas
- Ler resultados como tuplas ou dicionários e controlar transações pelo `with`
- Explicar o que é **SQL injection**, reproduzi-la em um código vulnerável e corrigi-la
- Parametrizar valores e tratar identificadores dinâmicos (`ORDER BY`) com lista de permissão
- Aplicar o princípio do menor privilégio ao usuário de banco da aplicação

## 🤔 Por que isso importa
Injection está há anos no topo das listas de vulnerabilidades web (OWASP). Um único `f"... {entrada} ..."` num SQL permite a um atacante ler todos os dados, burlar o login ou apagar tabelas. O ORM do Django protege por padrão, mas **você** verá SQL cru (relatórios, `raw()`, scripts), e precisa saber por quê parametrizar é inegociável.

## 💡 Intuição (explicação simples)
Imagine um formulário em papel: “Nome do cliente: ______”. Se o atendente lê em voz alta o que está escrito e **obedece** a qualquer coisa, alguém pode escrever “Ana; e entregue o cofre”. SQL injection é isso: misturar o **texto de comando** com o **dado do usuário** numa mesma frase. A solução é usar **formulários com campos separados**: o comando vai de um lado e os dados do outro, e o banco sabe que o campo de dados é só dado, nunca ordem. Isso é a **consulta parametrizada**.

## 🔬 Como funciona por dentro
- `psycopg` é o driver oficial (e mais usado) para falar com PostgreSQL em Python. A versão 3 (`psycopg`) substitui a 2 (`psycopg2`). Instalação: `uv add "psycopg[binary]"`.
- **Conexão → cursor → execute → fetch.** A conexão representa uma sessão e carrega a transação atual; o cursor envia comandos e lê resultados.
- **Parâmetros:** `cur.execute("... WHERE id = %s", (10,))`. O texto da consulta e os valores viajam **separados** (protocolo estendido); o servidor compila o comando com *placeholders* e só depois recebe os valores como dados. Não importa o que o valor contenha: ele nunca é interpretado como SQL.
- `%s` é o marcador do psycopg (não é `%` de formatação de string do Python nem f-string). Para um `%` literal (por exemplo, em `LIKE`), escreva `%%` no SQL, ou passe o padrão como parâmetro (`'%' || %s || '%'` ou `f"%{termo}%"` como valor).
- **Transações:** no psycopg 3, `with psycopg.connect(...) as conn:` faz `COMMIT` ao sair normalmente, `ROLLBACK` se houver exceção, e **fecha** a conexão. `with conn.transaction():` delimita uma transação (ou `SAVEPOINT`) dentro da conexão.
- **O que não dá para parametrizar:** nomes de tabelas e colunas (identificadores), `ORDER BY coluna`, direção `ASC/DESC`. Para esses casos: lista de permissão ou `psycopg.sql.Identifier`.

| Defesa | Protege de | Observação |
|---|---|---|
| Consultas **parametrizadas** | Injection em valores | A defesa principal e obrigatória |
| Lista de permissão (*allowlist*) | Injection em identificadores | Mapa `"preco" → "price"` |
| Menor privilégio no usuário do banco | Dano caso algo escape | App sem `DROP`/`CREATE`/`SUPERUSER` |
| Validação de entrada | Dados malformados | Complementa, **não substitui** a parametrização |
| ORM / *query builder* | Erro humano | Usa parâmetros por baixo |

## 🛠️ Exemplo prático
Banco `loja` (aula 03), container ligado. Dependência: `uv add "psycopg[binary]"`. Saídas reais.

**1. Conectar, consultar e ler o resultado**
```python
import psycopg

DSN = "postgresql://postgres:dev@localhost:5432/loja"       # usuário:senha@host:porta/banco

with psycopg.connect(DSN) as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT sku, name, price FROM products WHERE category_id = %s AND price < %s ORDER BY id LIMIT 3", (1, 150))
        print([c.name for c in cur.description], cur.rowcount)
        for linha in cur:                                    # cada linha é uma tupla
            print(linha)
        cur.execute("SELECT count(*) FROM products")
        print(cur.fetchone()[0])
```
```text
['sku', 'name', 'price'] 3
('PF-01', 'Mouse sem fio', Decimal('89.90'))
('PF-04', 'Teclado compacto', Decimal('149.90'))
('PF-06', 'Mousepad grande', Decimal('59.90'))
50
```
Repare: `price` volta como `Decimal('89.90')` (de `numeric`), `created_at` volta como `datetime` com fuso, e `NULL` vira `None`. O psycopg converte os tipos nos dois sentidos.

**2. Linhas como dicionários**
```python
import psycopg
from psycopg.rows import dict_row

with psycopg.connect(DSN, row_factory=dict_row) as conn:
    produto = conn.execute("SELECT id, sku, name, price, is_active FROM products WHERE sku = %(sku)s", {"sku": "MN-04"}).fetchone()
    print(produto)
    print(produto["name"], type(produto["price"]).__name__)
```
```text
{'id': 24, 'sku': 'MN-04', 'name': 'Monitor 27 polegadas 4K', 'price': Decimal('2199.00'), 'is_active': True}
Monitor 27 polegadas 4K Decimal
```
`%(nome)s` com um dict deixa a consulta legível quando há muitos parâmetros. `conn.execute(...)` é um atalho para criar o cursor e executar.

**3. Escrever dados: `INSERT ... RETURNING`, `commit` e `rollback`**
```python
with psycopg.connect(DSN, row_factory=dict_row) as conn:
    novo = conn.execute(
        "INSERT INTO categories (name, slug) VALUES (%s, %s) RETURNING id, name",
        ("Gamer", "gamer"),
    ).fetchone()
    print("criada:", novo)                                    # confirmada ao sair do with

try:
    with psycopg.connect(DSN) as conn:
        conn.execute("INSERT INTO categories (name, slug) VALUES (%s, %s)", ("Temporária", "temp"))
        conn.execute("INSERT INTO categories (name, slug) VALUES (%s, %s)", ("Gamer", "gamer"))   # slug repetido!
except psycopg.errors.UniqueViolation as e:
    print("erro:", type(e).__name__, "-", e.diag.constraint_name)

with psycopg.connect(DSN) as conn:
    print(conn.execute("SELECT name FROM categories WHERE slug IN ('gamer', 'temp') ORDER BY id").fetchall())
```
```text
criada: {'id': 6, 'name': 'Gamer'}
erro: UniqueViolation - categories_name_key
[('Gamer',)]
```
Como a segunda inserção falhou, o `with` fez **`ROLLBACK`** e a categoria “Temporária” também sumiu: atomicidade (aula 09). Os erros do banco viram exceções específicas (`UniqueViolation`, `ForeignKeyViolation`, `CheckViolation`…) em `psycopg.errors`.

**4. Transação explícita e vários comandos**
```python
with psycopg.connect(DSN) as conn:
    with conn.transaction():                                  # BEGIN ... COMMIT
        conn.execute("UPDATE products SET stock = stock - %s WHERE id = %s AND stock >= %s", (2, 1, 2))
        conn.execute("UPDATE products SET stock = stock - %s WHERE id = %s AND stock >= %s", (1, 1, 1))
    print(conn.execute("SELECT stock FROM products WHERE id = 1").fetchone())
    with conn.cursor() as cur:
        cur.execute("CREATE TEMP TABLE lote (sku text, qtd int)")
        cur.executemany("INSERT INTO lote VALUES (%s, %s)", [("A", 1), ("B", 2), ("C", 3)])   # um comando, vários conjuntos de parâmetros
        print("linhas inseridas:", cur.rowcount, "| soma:", cur.execute("SELECT sum(qtd) FROM lote").fetchone()[0])
```
```text
(1,)
linhas inseridas: 3 | soma: 6
```
### 🔓 SQL injection: o código vulnerável

Preparamos uma tabela de demonstração (nunca guarde senha em texto puro: usamos só para ilustrar; hash de senha é tema do Módulo 9):
```python
with psycopg.connect(DSN) as conn:
    conn.execute("DROP TABLE IF EXISTS demo_users")
    conn.execute("CREATE TABLE demo_users (id serial PRIMARY KEY, email text UNIQUE, password text, is_admin boolean)")
    conn.execute("INSERT INTO demo_users (email, password, is_admin) VALUES ('admin@minishop.test', 'segredo-do-admin', true), ('ana@exemplo.test', 'senha-da-ana', false)")
print("tabela de demonstração criada")
```
```text
tabela de demonstração criada
```
**A busca vulnerável (concatenando texto):**
```python
def buscar_vulneravel(conn, termo):
    sql = f"SELECT sku, name, price FROM products WHERE name ILIKE '%{termo}%' AND is_active ORDER BY id"
    return conn.execute(sql).fetchall()

with psycopg.connect(DSN) as conn:
    print("busca normal  :", buscar_vulneravel(conn, "mousepad"))
    print("ataque 1 (tudo):", len(buscar_vulneravel(conn, "x' OR 1=1 --")), "linhas (OR 1=1 vale sempre e o -- comentou o AND is_active: vieram até os inativos!)")
    print("ataque 2 (UNION, vaza e-mails):")
    for linha in buscar_vulneravel(conn, "zzz' UNION SELECT email, name, 0 FROM users --")[:3]:
        print("  ", linha)
    print("ataque 3 (dados de outra tabela, a senha!):")
    print("  ", buscar_vulneravel(conn, "zzz' UNION SELECT email, password, 0 FROM demo_users --"))
```
```text
busca normal  : [('PF-06', 'Mousepad grande', Decimal('59.90'))]
ataque 1 (tudo): 50 linhas (OR 1=1 vale sempre e o -- comentou o AND is_active: vieram até os inativos!)
ataque 2 (UNION, vaza e-mails):
   ('carla@exemplo.test', 'Carla Mendes', Decimal('0'))
   ('elisa@exemplo.test', 'Elisa Prado', Decimal('0'))
   ('bruno@exemplo.test', 'Bruno Lima', Decimal('0'))
ataque 3 (dados de outra tabela, a senha!):
   [('admin@minishop.test', 'segredo-do-admin', Decimal('0')), ('ana@exemplo.test', 'senha-da-ana', Decimal('0'))]
```
O que aconteceu no ataque 2: o SQL final foi `... ILIKE '%zzz' UNION SELECT email, name, 0 FROM users --%' AND is_active ...`. As aspas do atacante **fecharam** o texto, o `UNION` colou outra consulta e o `--` comentou o resto. O atacante enxerga o que o banco permite à conta da aplicação.
**Aspas legítimas também quebram o código (um bug, além da brecha):**
```python
with psycopg.connect(DSN) as conn:
    buscar_vulneravel(conn, "O'Reilly")
```
```text
SyntaxError: syntax error at or near "Reilly"
LINE 1: ...u, name, price FROM products WHERE name ILIKE '%O'Reilly%' A...
                                                             ^
```
**Login que aceita qualquer um:**
```python
def login_vulneravel(conn, email, senha):
    sql = f"SELECT id, email, is_admin FROM demo_users WHERE email = '{email}' AND password = '{senha}'"
    return conn.execute(sql).fetchone()

with psycopg.connect(DSN) as conn:
    print("senha errada      :", login_vulneravel(conn, "admin@minishop.test", "chute"))
    print("senha certa       :", login_vulneravel(conn, "admin@minishop.test", "segredo-do-admin"))
    print("ataque (comentário):", login_vulneravel(conn, "admin@minishop.test' --", "qualquer coisa"))
    print("ataque (OR)        :", login_vulneravel(conn, "x", "x' OR is_admin = true --"))
```
```text
senha errada      : None
senha certa       : (1, 'admin@minishop.test', True)
ataque (comentário): (1, 'admin@minishop.test', True)
ataque (OR)        : (1, 'admin@minishop.test', True)
```
`admin@minishop.test' --` corta a verificação de senha com o comentário `--`. **Entrou como administrador sem saber a senha.**

**Dano destrutivo (várias instruções):**
```python
with psycopg.connect(DSN) as conn:
    conn.execute(f"SELECT * FROM demo_users WHERE email = '{chr(39)}; DROP TABLE demo_users; --'")     # atacante digitou: '; DROP TABLE demo_users; --
    existe = conn.execute("SELECT to_regclass('demo_users')").fetchone()[0]
print("tabela demo_users ainda existe?", existe)
```
```text
tabela demo_users ainda existe? None
```
(`chr(39)` é a aspa simples; a entrada do atacante foi `'; DROP TABLE demo_users; --`.) A tabela foi **apagada** pela consulta de busca.

### 🔒 A correção: consultas parametrizadas
```python
with psycopg.connect(DSN) as conn:
    conn.execute("DROP TABLE IF EXISTS demo_users")
    conn.execute("CREATE TABLE demo_users (id serial PRIMARY KEY, email text UNIQUE, password text, is_admin boolean)")
    conn.execute("INSERT INTO demo_users (email, password, is_admin) VALUES ('admin@minishop.test', 'segredo-do-admin', true)")

def buscar(conn, termo):
    return conn.execute("SELECT sku, name, price FROM products WHERE name ILIKE %s AND is_active ORDER BY id",
                        (f"%{termo}%",)).fetchall()            # o curinga faz parte do VALOR

def login(conn, email, senha):
    return conn.execute("SELECT id, email, is_admin FROM demo_users WHERE email = %s AND password = %s",
                        (email, senha)).fetchone()

with psycopg.connect(DSN) as conn:
    print("busca normal  :", buscar(conn, "mousepad"))
    print("ataque 1      :", buscar(conn, "x' OR 1=1 --"))
    print("ataque UNION  :", buscar(conn, "zzz' UNION SELECT email, password, 0 FROM demo_users --"))
    print("O'Reilly      :", buscar(conn, "O'Reilly"))             # agora é só texto, e funciona
    print("login legítimo:", login(conn, "admin@minishop.test", "segredo-do-admin"))
    print("login ataque  :", login(conn, "admin@minishop.test' --", "x"), login(conn, "x", "x' OR is_admin = true --"))
    print("tabela intacta:", conn.execute("SELECT to_regclass('demo_users')").fetchone()[0])
```
```text
busca normal  : [('PF-06', 'Mousepad grande', Decimal('59.90'))]
ataque 1      : []
ataque UNION  : []
O'Reilly      : []
login legítimo: (1, 'admin@minishop.test', True)
login ataque  : None None
tabela intacta: demo_users
```
Todas as entradas hostis viraram **apenas texto procurado**: o banco procura um produto cujo nome contém literalmente `x' OR '1'='1`, e não encontra.

**Identificadores dinâmicos (`ORDER BY`) com lista de permissão**
```python
from psycopg import sql

ORDENACOES = {"nome": "name", "preco": "price", "estoque": "stock"}          # entrada do usuário → coluna real

def listar(conn, ordem="nome", direcao="asc", limite=3):
    coluna = ORDENACOES.get(ordem)
    if coluna is None or direcao.lower() not in ("asc", "desc"):
        raise ValueError("ordenação inválida")
    consulta = sql.SQL("SELECT sku, {col} FROM products ORDER BY {col} {dir}, id LIMIT %s").format(
        col=sql.Identifier(coluna), dir=sql.SQL(direcao.upper()))
    return conn.execute(consulta, (limite,)).fetchall()

with psycopg.connect(DSN) as conn:
    print(listar(conn, "preco", "desc"))
    try:
        listar(conn, "price; DROP TABLE products; --")
    except ValueError as e:
        print("rejeitado:", e)
```
```text
[('MN-10', Decimal('2899.00')), ('MN-04', Decimal('2199.00')), ('MN-05', Decimal('1899.00'))]
rejeitado: ordenação inválida
```
`sql.Identifier` coloca aspas corretas no nome da coluna; mas o que realmente protege é o mapa de valores permitidos: **nunca** repasse o texto do usuário como identificador.

**Menor privilégio: mesmo que algo escape, o estrago é limitado**
```sql
DO $$ BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'app_user') THEN CREATE ROLE app_user LOGIN PASSWORD 'app'; END IF;
END $$;                                   -- (papéis são do servidor inteiro; o IF evita erro ao repetir)
GRANT CONNECT ON DATABASE loja TO app_user;
GRANT USAGE ON SCHEMA public TO app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO app_user;
\du app_user
```
```text
     List of roles
 Role name | Attributes 
-----------+------------
 app_user  |
```
```python
APP = "postgresql://app_user:app@localhost:5432/loja"
with psycopg.connect(APP) as conn:
    print("app_user lê  :", conn.execute("SELECT count(*) FROM products").fetchone()[0], "produtos")
    try:
        conn.execute("DROP TABLE products")
    except psycopg.errors.InsufficientPrivilege as e:
        print("app_user não pode apagar tabelas ->", type(e).__name__)
```
```text
app_user lê  : 50 produtos
app_user não pode apagar tabelas -> InsufficientPrivilege
```
A aplicação deve conectar com um usuário que só tem os privilégios necessários (nunca o `postgres`/dono do schema). As **migrações** (que criam tabelas) rodam com outro usuário.

## ⚠️ Erros comuns e boas práticas
| Mensagem / sintoma | Causa | Solução |
|---|---|---|
| `psycopg.OperationalError: connection failed: Connection refused` | Banco desligado ou porta errada | `docker start minishop-pg`; confira o DSN |
| `psycopg.OperationalError: ... password authentication failed` | Senha/usuário errados | Confira o DSN |
| `psycopg.errors.UndefinedTable: relation "x" does not exist` | Banco/schema errado | Confira o nome do banco no DSN |
| `psycopg.ProgrammingError: the query has 2 placeholders but 1 parameters were passed` | Número de `%s` diferente do de valores | Alinhe-os; lembre `(valor,)` com vírgula para um só |
| `TypeError: ... not all arguments converted` / valor sem vírgula `("x")` | `("x")` é string, não tupla | `("x",)` |
| `psycopg.errors.SyntaxError` com apóstrofo no texto | Concatenação de string (e uma brecha!) | Parametrize |
| Dados “sumiram” depois do script | Esqueceu o `COMMIT` (conexão sem `with`) | Use `with psycopg.connect(...)` |
| `current transaction is aborted` | Erro dentro de transação não tratado | `ROLLBACK`/`with conn.transaction()` |

- **Nunca** monte SQL com f-string, `+`, `%` ou `.format()` usando entrada de usuário. Sem exceções: nem “só números”, nem “vem do nosso front”.
- **Sempre** passe valores como parâmetros; para identificadores, lista de permissão.
- A aplicação conecta com **menor privilégio**; senha e DSN vêm de **variável de ambiente**, nunca do código (Módulo 5/9).
- Não mostre mensagens de erro do banco ao usuário (podem revelar a estrutura das tabelas).
- Ferramentas como `sqlmap` e revisão de código (`grep -n 'execute(f"'`) ajudam a achar injeções.

## 🧠 Pausa para lógica
**Problema (filtros dinâmicos sem concatenar valores).** Escreva `construir_consulta(busca=None, preco_min=None, preco_max=None, categoria=None)` que monta o `WHERE` só com os filtros informados e devolve `(sql, parametros)`. O SQL só pode conter texto **fixo** (vindo do seu código) e `%s`; todos os valores vão em `parametros`.

<details><summary>Dica</summary>
Uma lista de <code>condicoes</code> (textos fixos com <code>%s</code>) e uma lista de <code>params</code>. No fim: <code>" AND ".join(condicoes)</code>. Pergunta-chave: algum pedaço do SQL final depende do texto do usuário? A resposta deve ser “não”.
</details>

<details><summary>Solução comentada</summary>

```python
def construir_consulta(busca=None, preco_min=None, preco_max=None, categoria=None):
    condicoes, params = ["is_active"], []
    if busca:
        condicoes.append("name ILIKE %s");   params.append(f"%{busca}%")
    if preco_min is not None:
        condicoes.append("price >= %s");     params.append(preco_min)
    if preco_max is not None:
        condicoes.append("price <= %s");     params.append(preco_max)
    if categoria is not None:
        condicoes.append("category_id = %s"); params.append(categoria)
    return "SELECT sku, name, price FROM products WHERE " + " AND ".join(condicoes) + " ORDER BY price, id", params

for kwargs in ({}, {"busca": "cabo", "preco_max": 30}, {"busca": "x' OR 1=1 --", "categoria": 4}):
    sql_, params = construir_consulta(**kwargs)
    print(sql_.split("WHERE")[1].split("ORDER")[0].strip(), params)

with psycopg.connect(DSN) as conn:
    sql_, params = construir_consulta(busca="cabo", preco_max=30)
    print(conn.execute(sql_, params).fetchall())
```
```text
is_active []
is_active AND name ILIKE %s AND price <= %s ['%cabo%', 30]
is_active AND name ILIKE %s AND category_id = %s ["%x' OR 1=1 --%", 4]
[('CB-04', 'Cabo USB-C 1m', Decimal('24.90')), ('CB-06', 'Cabo de rede Cat6 5m', Decimal('27.90')), ('CB-01', 'Cabo HDMI 2m', Decimal('29.90'))]
```
O texto do atacante só aparece em `params`, jamais na string SQL. É a ideia por trás do `QuerySet.filter()` do Django (Módulo 5).
</details>

**Variação mais difícil:** acrescente `ordem` (com lista de permissão) e paginação (`LIMIT %s OFFSET %s`) sem quebrar a regra de “nenhum valor na string SQL”.

## 🧩 Exercícios
**1. Fixação**
(a) Por que `("x")` não funciona como parâmetro e `("x",)` sim? (b) O que acontece com `%` literal num SQL com parâmetros? (c) Por que `ORDER BY %s` com o nome da coluna como parâmetro não ordena como esperado?

<details><summary>Solução</summary>

(a) `("x")` é só uma string entre parênteses; um parâmetro único precisa de uma tupla (vírgula). (b) Precisa ser `%%`, senão o driver o confunde com um marcador. (c) Parâmetros são **valores**, não identificadores: `ORDER BY 'price'` ordena por uma constante (nada muda). Para a coluna use lista de permissão + `sql.Identifier`.
</details>

**2. Aplicação no projeto MiniShop**
Crie o pacote `minishop_db/` com acesso ao banco **sem injeção**, reaproveitando as consultas SQL das aulas 04 a 09.

Critérios de pronto:
- [ ] `minishop_db/conexao.py` lê o DSN de `DATABASE_URL` (variável de ambiente), com padrão para o container local
- [ ] `minishop_db/produtos.py` com `listar(conn, busca, preco_min, preco_max, categoria, ordem, pagina, tamanho)` (filtros dinâmicos, lista de permissão para ordem, `LIMIT/OFFSET` parametrizados), `obter(conn, sku)` e `criar(conn, ...)` com `RETURNING`
- [ ] `minishop_db/pedidos.py` com `criar_pedido(conn, user_id)` usando `conn.transaction()` e a lógica da aula 09 (atualização condicional do estoque, `ROLLBACK` se faltar estoque, exceção `EstoqueInsuficiente`)
- [ ] Testes pytest contra o container: cada teste roda numa transação que é desfeita no final (fixture `conn` com `conn.rollback()`), incluindo **testes de injeção** (entradas como `x' OR 1=1 --` não retornam tudo)
- [ ] Uso de `psycopg.sql.Identifier` ou allowlist onde há identificador dinâmico, nenhum f-string com valor de usuário (`grep -n 'execute(f' -r minishop_db` não acha nada)
- [ ] Usuário de aplicação `app_user` (menor privilégio) usado nos testes de leitura
- [ ] Commit `feat(db): add psycopg data access layer`

<details><summary>Solução de referência</summary>

```python
import os
import psycopg
from decimal import Decimal
from psycopg.rows import dict_row

class EstoqueInsuficiente(Exception):
    pass

def conectar(dsn=None):
    return psycopg.connect(dsn or os.environ.get("DATABASE_URL", "postgresql://postgres:dev@localhost:5432/loja"), row_factory=dict_row)

def criar_pedido(conn, user_id: int) -> dict:
    with conn.transaction():                                          # tudo ou nada
        itens = conn.execute(
            "SELECT ci.product_id, ci.quantity, p.price FROM carts c JOIN cart_items ci ON ci.cart_id = c.id "
            "JOIN products p ON p.id = ci.product_id WHERE c.user_id = %s ORDER BY ci.product_id", (user_id,)).fetchall()
        if not itens:
            raise ValueError("carrinho vazio")
        total = sum(i["quantity"] * i["price"] for i in itens)
        pedido = conn.execute("INSERT INTO orders (user_id, status, total) VALUES (%s, 'pending', %s) RETURNING id, total",
                              (user_id, total)).fetchone()
        for i in itens:
            baixa = conn.execute("UPDATE products SET stock = stock - %s WHERE id = %s AND stock >= %s",
                                 (i["quantity"], i["product_id"], i["quantity"]))
            if baixa.rowcount == 0:
                raise EstoqueInsuficiente(f"produto {i['product_id']} sem estoque suficiente")   # sai do with: ROLLBACK
            conn.execute("INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES (%s, %s, %s, %s)",
                         (pedido["id"], i["product_id"], i["quantity"], i["price"]))
        conn.execute("DELETE FROM cart_items WHERE cart_id IN (SELECT id FROM carts WHERE user_id = %s)", (user_id,))
        return pedido

with conectar() as conn:
    conn.execute("UPDATE products SET stock = 0 WHERE id = 7")        # força a falta de estoque do item 2 do carrinho
    antes = conn.execute("SELECT count(*) AS n FROM orders WHERE user_id = 2").fetchone()["n"]
    try:
        criar_pedido(conn, 2)
    except EstoqueInsuficiente as e:
        print("falhou:", e)
    depois = conn.execute("SELECT count(*) AS n FROM orders WHERE user_id = 2").fetchone()["n"]
    print("pedidos do usuário 2: antes =", antes, "| depois =", depois, "(nenhum pedido pela metade)")
    conn.rollback()                                                   # desfaz o UPDATE do teste
```
```text
falhou: produto 7 sem estoque suficiente
pedidos do usuário 2: antes = 7 | depois = 7 (nenhum pedido pela metade)
```
O padrão da fixture de testes: abrir uma conexão, entregar ao teste e, ao final, `conn.rollback()`: nenhum teste deixa lixo no banco.
</details>

**3. Desafio (opcional)**
Use `psycopg_pool.ConnectionPool` para reaproveitar conexões e meça o tempo de 200 consultas com e sem *pool*. Por que abrir uma conexão por requisição é caro?

## 🎤 Na entrevista
- **O que é SQL injection e como evitar?** Quando entrada do usuário é concatenada ao SQL e alterada a sua estrutura. Evita-se com **consultas parametrizadas** (valores separados do comando), lista de permissão para identificadores, menor privilégio no usuário do banco e uso de ORM/*query builders*.
- **Por que validar a entrada não basta?** Validação filtra o esperado e falha com casos inesperados; a parametrização elimina a classe inteira de problemas porque o dado nunca é interpretado como SQL.
- **Como parametrizar um nome de coluna em `ORDER BY`?** Não dá para usar `%s`; mapeie a entrada para uma coluna permitida (`dict`) e use `sql.Identifier`/constantes do seu código.
- **O que o `with psycopg.connect()` faz?** Confirma (`COMMIT`) ao sair normalmente, desfaz (`ROLLBACK`) em exceção e fecha a conexão.

## 📚 Para ir além
- 📄 Documentação oficial: [psycopg 3](https://www.psycopg.org/psycopg3/docs/). Guia básico, parâmetros, transações, `row_factory`, `sql`.
- 📄 Documentação oficial: [OWASP: SQL Injection](https://owasp.org/www-community/attacks/SQL_Injection). Descrição do ataque, exemplos e prevenção.
- 📄 Documentação oficial: [Privilégios no PostgreSQL](https://www.postgresql.org/docs/current/ddl-priv.html). `GRANT`, `REVOKE`, papéis.
- 🏋️ Prática extra: rode `grep -rn 'execute(f' .` em projetos seus ou de código aberto e veja se algum f-string recebe entrada externa.

## ✅ Checklist da aula
- [ ] Conectei com `psycopg` e usei parâmetros `%s`
- [ ] Reproduzi as injeções (tudo, UNION, login, DROP) e as bloqueei
- [ ] Usei lista de permissão no `ORDER BY`
- [ ] Criei o `app_user` com menor privilégio
- [ ] Entreguei `minishop_db/` com testes
