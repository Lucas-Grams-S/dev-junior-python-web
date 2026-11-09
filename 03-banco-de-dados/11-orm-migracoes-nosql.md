# 11. ORM, migrações e noção de NoSQL (Redis, MongoDB)

> ⏱️ ~1h30 · Módulo 3 · Pré-requisitos: [10](10-psycopg-sql-injection.md); classes ([1.12](../01-python-logica/12-poo-classes.md)) e dicts ([1.06](../01-python-logica/06-dicts-sets.md))

## 🎯 Objetivos
Ao final desta aula você consegue:
- Explicar o que é um ORM, o problema que resolve e os custos que traz
- Construir, em miniatura, o mecanismo central de um ORM (classe ↔ tabela) para entender o que o Django faz
- Explicar o que é uma migração e por que o schema do banco deve ser versionado
- Implementar um executor de migrações simples e idempotente
- Dizer quando faz sentido usar Redis, MongoDB ou `jsonb` no PostgreSQL, sem se deixar levar por moda

## 🤔 Por que isso importa
No Módulo 5 você usará o ORM do Django e as migrações dele: `Product.objects.filter(...)` e `python manage.py migrate`. Quem só decorou os comandos fica perdido quando a consulta fica lenta (N+1), quando uma migração falha em produção ou quando surge a pergunta “por que não usar MongoDB?”. Esta aula dá o modelo mental.

## 💡 Intuição (explicação simples)
- **ORM** = um **intérprete** entre dois idiomas: o seu (objetos Python: `produto.preco`) e o do banco (tabelas e SQL). Você fala em Python; ele traduz para SQL e traduz as respostas de volta para objetos. Intérpretes são cômodos, mas **perdem nuances**: às vezes a tradução é desajeitada, e você precisa conferir o que foi dito (o SQL gerado).
- **Migração** = o **diário de obras do banco**. Cada reforma (criar tabela, adicionar coluna) é registrada em ordem, com número. Qualquer pessoa, em qualquer máquina, reproduz a obra inteira aplicando o diário do início ao fim, e sabe em que página (versão) o banco está.
- **NoSQL** = outras **ferramentas na caixa**: nem todo prego pede o mesmo martelo.

## 🔬 Como funciona por dentro
**ORM (*Object-Relational Mapping*).**
- *Mapeamento:* classe ↔ tabela, atributo ↔ coluna, objeto ↔ linha, FK ↔ referência a outro objeto.
- *Padrões:* **Active Record** (o objeto sabe se salvar: `produto.save()`; usado pelo Django) e **Data Mapper** (um mapeador separado persiste objetos simples; usado pelo SQLAlchemy).
- *O que ele entrega:* menos código repetitivo; **consultas parametrizadas por padrão** (segurança, aula 10); portabilidade entre bancos; relacionamentos navegáveis; **migrações** geradas a partir dos modelos.
- *O que cobra:* **N+1 consultas** (uma por item de uma lista, aula 5.7); SQL gerado pouco óbvio e às vezes ineficiente; abstração que “vaza” (você ainda precisa saber SQL e índices); consultas muito complexas ficam mais claras em SQL puro.
- *Regra prática:* use o ORM para o dia a dia (CRUD, filtros, relacionamentos) e SQL cru (com parâmetros) para relatórios pesados. Sempre **olhe o SQL gerado** nas telas críticas.

**Migrações.** Um arquivo por mudança, numerado e **imutável depois de aplicado**; uma tabela de controle (`schema_migrations`) guarda quais já rodaram; aplicar = rodar as pendentes, em ordem, cada uma numa transação. Benefícios: ambientes iguais (dev, CI, produção), histórico revisável no Git, deploy automatizável. No Django: `makemigrations` (gera o arquivo a partir da diferença entre os modelos e o estado anterior) e `migrate` (aplica). No SQLAlchemy: Alembic.

```mermaid
flowchart LR
    M1[001_create_reviews.sql] --> M2[002_add_coupons.sql] --> M3[003_add_index.sql]
    M1 -.registrada.-> T[(schema_migrations)]
    M2 -.registrada.-> T
    M3 -. pendente: será aplicada .-> T
```
**Mudanças seguras de schema em produção:** adicionar coluna **nula** ou com padrão é barato; renomear/remover coluna quebra o código antigo em execução (faça em duas etapas: o código deixa de usar, depois remove); `CREATE INDEX CONCURRENTLY`; constraints `NOT VALID` + `VALIDATE` (aula 08).

**NoSQL** (*not only SQL*): famílias e usos típicos:

| Família | Exemplo | Bom para | Cuidado |
|---|---|---|---|
| Chave-valor | **Redis** | cache, sessões, contadores, filas, *rate limiting* (tudo em memória, muito rápido) | dados voláteis por padrão; consultas só por chave |
| Documento | **MongoDB** | documentos JSON flexíveis, esquemas que mudam muito, catálogo heterogêneo | relações e transações multi-documento são mais frágeis; consistência por sua conta |
| Colunar | Cassandra | enormes volumes de escrita | modelagem orientada às consultas |
| Grafo | Neo4j | relações profundas (redes sociais) | nicho |
| Busca | Elasticsearch/OpenSearch | busca textual, logs | não é fonte da verdade |

Para a maioria dos sistemas web, **PostgreSQL resolve quase tudo** (inclusive JSON com `jsonb`). Outros bancos entram como **complemento** (Redis para cache e filas), não como substituição. O teorema CAP resume o dilema dos sistemas distribuídos: diante de uma partição de rede, escolha entre consistência e disponibilidade.

## 🛠️ Exemplo prático
Banco `loja` (aula 03); `uv add "psycopg[binary]"`.

**1. Um ORM em miniatura (para perder o medo)**
```python
import psycopg

DSN = "postgresql://postgres:dev@localhost:5432/loja"
OPERADORES = {"exact": "=", "lt": "<", "lte": "<=", "gt": ">", "gte": ">=", "contains": "ILIKE"}


class Model:
    table: str
    columns: tuple[str, ...]
    ultimo_sql = ""

    def __init__(self, **dados):
        for coluna in self.columns:
            setattr(self, coluna, dados.get(coluna))

    def __repr__(self):
        return f"<{type(self).__name__} " + " ".join(f"{c}={getattr(self, c)!r}" for c in self.columns[:3]) + ">"

    @classmethod
    def filter(cls, order_by=None, limit=None, **filtros):
        condicoes, params = [], []
        for chave, valor in filtros.items():
            coluna, _, op = chave.partition("__")
            if coluna not in cls.columns:                    # lista de permissão: o nome da coluna nunca vem "solto"
                raise AttributeError(f"{cls.__name__} não tem a coluna '{coluna}'")
            condicoes.append(f"{coluna} {OPERADORES[op or 'exact']} %s")
            params.append(f"%{valor}%" if op == "contains" else valor)
        sql = f"SELECT {', '.join(cls.columns)} FROM {cls.table}"
        if condicoes:
            sql += " WHERE " + " AND ".join(condicoes)
        if order_by:
            coluna = order_by.lstrip("-")
            if coluna not in cls.columns:
                raise AttributeError(coluna)
            sql += f" ORDER BY {coluna}" + (" DESC" if order_by.startswith("-") else "")
        if limit:
            sql += f" LIMIT {int(limit)}"
        cls.ultimo_sql = sql
        with psycopg.connect(DSN) as conn:
            return [cls(**dict(zip(cls.columns, linha))) for linha in conn.execute(sql, params)]

    def save(self):
        """Active Record: o objeto sabe se gravar."""
        dados = {c: getattr(self, c) for c in self.columns if c != "id"}
        with psycopg.connect(DSN) as conn:
            if self.id is None:
                cols = ", ".join(dados)
                marcadores = ", ".join(["%s"] * len(dados))
                self.id = conn.execute(f"INSERT INTO {self.table} ({cols}) VALUES ({marcadores}) RETURNING id", list(dados.values())).fetchone()[0]
            else:
                sets = ", ".join(f"{c} = %s" for c in dados)
                conn.execute(f"UPDATE {self.table} SET {sets} WHERE id = %s", [*dados.values(), self.id])
        return self


class Product(Model):
    table = "products"
    columns = ("id", "sku", "name", "price", "stock", "is_active")
```
```python
from mini_orm import Product

baratos = Product.filter(is_active=True, price__lt=40, order_by="-price", limit=3)
print(Product.ultimo_sql)
print(baratos)

mouse = Product.filter(name__contains="mouse gamer")[0]
mouse.price = mouse.price - 10
mouse.save()
print(Product.filter(sku="PF-02")[0].price)
try:
    Product.filter(preco=10)
except AttributeError as e:
    print("erro:", e)
```
```text
SELECT id, sku, name, price, stock, is_active FROM products WHERE is_active = %s AND price < %s ORDER BY price DESC LIMIT 3
[<Product id=9 sku='PF-09' name='Leitor de cartão SD'>, <Product id=37 sku='CB-07' name='Adaptador HDMI para VGA'>, <Product id=47 sku='AR-07' name='Pen drive 64 GB'>]
149.90
erro: Product não tem a coluna 'preco'
```
(O `save()` alterou o preço de `PF-02` no seu banco: para restaurar, recarregue o `loja.sql`.) Em ~50 linhas você reproduziu a essência: **traduzir chamadas de método em SQL parametrizado**, mapear linhas para objetos e gravar de volta. O ORM real faz isto com muito mais recursos (relacionamentos, *lazy loading*, otimizações, vários bancos). Repare em `price__lt=40`: a mesma sintaxe do Django.

**2. O ORM do Django, de verdade, sobre o mesmo banco** (prévia: a configuração do Django virá no Módulo 5)

Usando o Django 5.2 apenas como biblioteca (`uv add "django==5.2.*"`), com modelos “não gerenciados” (`managed = False`: o Django **não** cria nem altera a tabela) mapeados nas tabelas que já existem. Precisamos de um “app” mínimo, uma pasta vazia com `__init__.py`:
```python
```
```python
import django
from django.conf import settings

settings.configure(DATABASES={"default": {"ENGINE": "django.db.backends.postgresql", "NAME": "loja", "USER": "postgres",
                                          "PASSWORD": "dev", "HOST": "localhost", "PORT": "5432"}},
                   INSTALLED_APPS=["demoapp"], DEFAULT_AUTO_FIELD="django.db.models.AutoField", USE_TZ=True)
django.setup()

from django.db import models, connection, reset_queries
from django.db.models import Count


class Category(models.Model):
    name = models.TextField()
    class Meta: app_label = "demoapp"; managed = False; db_table = "categories"


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.DO_NOTHING, db_column="category_id", related_name="products")
    sku = models.TextField(); name = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2); is_active = models.BooleanField()
    class Meta: app_label = "demoapp"; managed = False; db_table = "products"


qs = Product.objects.filter(is_active=True, price__lt=100).order_by("-price")[:3]
print(qs.query)                                       # o SQL que o Django vai enviar
print(list(qs.values_list("sku", "price")))

print(Category.objects.annotate(n=Count("products")).order_by("-n", "id").query)
print(list(Category.objects.annotate(n=Count("products")).order_by("id").values_list("name", "n")))
```
```text
SELECT "products"."id", "products"."category_id", "products"."sku", "products"."name", "products"."price", "products"."is_active" FROM "products" WHERE ("products"."is_active" AND "products"."price" < 100) ORDER BY "products"."price" DESC LIMIT 3
[('AR-10', Decimal('99.90')), ('AU-07', Decimal('99.90')), ('PF-01', Decimal('89.90'))]
SELECT "categories"."id", "categories"."name", COUNT("products"."id") AS "n" FROM "categories" LEFT OUTER JOIN "products" ON ("categories"."id" = "products"."category_id") GROUP BY "categories"."id", "categories"."name" ORDER BY 3 DESC, "categories"."id" ASC
[('Periféricos', 10), ('Áudio', 10), ('Monitores', 10), ('Cabos e adaptadores', 10), ('Armazenamento', 10)]
```
Compare com o seu SQL das aulas 04 a 06: é o mesmo. O ORM é só uma forma de escrevê-lo em Python.

**3. O custo: o problema N+1 (olhando o número de consultas)**
```python
reset_queries()
settings.DEBUG = True                                # habilita o registro de consultas
nomes = [(p.sku, p.category.name) for p in Product.objects.all()[:10]]     # 1 consulta + 1 por produto
print("sem otimização:", len(connection.queries), "consultas")
reset_queries()
nomes = [(p.sku, p.category.name) for p in Product.objects.select_related("category")[:10]]   # JOIN
print("com select_related:", len(connection.queries), "consulta")
```
```text
sem otimização: 11 consultas
com select_related: 1 consulta
```
Dez produtos, onze consultas: com 10 mil, são 10.001 idas ao banco. `select_related`/`prefetch_related` (Módulo 5, aula 7) resolvem. **Sempre olhe o número de consultas** de uma tela.

**4. Migrações: um executor em miniatura**
```sql
CREATE TABLE coupons (
    id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    code text NOT NULL UNIQUE,
    percent integer NOT NULL CHECK (percent BETWEEN 1 AND 90),
    valid_until date
);
```
```sql
ALTER TABLE coupons ADD COLUMN min_order numeric(10,2) NOT NULL DEFAULT 0;
INSERT INTO coupons (code, percent, min_order) VALUES ('BEMVINDO10', 10, 50.00);
```
```python
import sys
from pathlib import Path

import psycopg

DSN = "postgresql://postgres:dev@localhost:5432/loja"


def migrar(pasta="migracoes"):
    aplicadas = []
    with psycopg.connect(DSN) as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS schema_migrations (version text PRIMARY KEY, applied_at timestamptz NOT NULL DEFAULT now())")
        conn.commit()
        feitas = {r[0] for r in conn.execute("SELECT version FROM schema_migrations")}
        for arquivo in sorted(Path(pasta).glob("*.sql")):          # a ordem é o número no nome
            if arquivo.stem in feitas:
                continue
            with conn.transaction():                                # cada migração é atômica
                conn.execute(arquivo.read_text(encoding="utf-8"))
                conn.execute("INSERT INTO schema_migrations (version) VALUES (%s)", (arquivo.stem,))
            aplicadas.append(arquivo.stem)
    return aplicadas


if __name__ == "__main__":
    novas = migrar(*sys.argv[1:])
    print("aplicadas:", novas or "nada a fazer")
```
```bash
python migrar.py
python migrar.py          # de novo: idempotente
cat > migracoes/003_index_coupon_validity.sql <<'SQL'
CREATE INDEX coupons_valid_until_idx ON coupons (valid_until) WHERE valid_until IS NOT NULL;
SQL
python migrar.py          # só a nova
docker exec minishop-pg psql -U postgres -d loja -X -c "SELECT version FROM schema_migrations ORDER BY version" -c "SELECT code, percent, min_order FROM coupons"
```
```text
aplicadas: ['001_create_coupons', '002_add_coupon_min_order']
aplicadas: nada a fazer
aplicadas: ['003_index_coupon_validity']
          version          
---------------------------
 001_create_coupons
 002_add_coupon_min_order
 003_index_coupon_validity
(3 rows)

    code    | percent | min_order 
------------+---------+-----------
 BEMVINDO10 |      10 |     50.00
(1 row)
```
Cada arquivo roda numa transação junto com o registro em `schema_migrations`: se a migração falhar no meio, nada fica aplicado (o `COMMIT` leva as duas coisas). **Regra de ouro:** nunca edite uma migração já aplicada; crie outra.

**5. Uma migração que falha: atomicidade**
```bash
cat > migracoes/004_quebrada.sql <<'SQL'
ALTER TABLE coupons ADD COLUMN notes text;
INSERT INTO coupons (code, percent) VALUES ('ABSURDO', 99);   -- viola o CHECK (1..90)
SQL
python migrar.py 2>&1 | tail -n 2
docker exec minishop-pg psql -U postgres -d loja -X -c "SELECT count(*) AS coluna_notes_existe FROM information_schema.columns WHERE table_name = 'coupons' AND column_name = 'notes'"
rm migracoes/004_quebrada.sql
```
```text
psycopg.errors.CheckViolation: new row for relation "coupons" violates check constraint "coupons_percent_check"
DETAIL:  Failing row contains (2, ABSURDO, 99, null, 0.00, null).
 coluna_notes_existe 
---------------------
                   0
(1 row)
```
Como o PostgreSQL permite DDL transacional, a coluna `notes` **não** foi criada: tudo ou nada. (Nem todo banco faz isso; no MySQL, por exemplo, a maioria dos DDLs confirma na hora.)

**6. NoSQL: Redis (chave-valor em memória)** — container `redis:8`, comandos reais:
```bash
R="docker exec minishop-redis redis-cli"
$R SET produto:PF-01:preco "89.90"
$R GET produto:PF-01:preco
$R INCR visitas:home; $R INCR visitas:home; $R INCRBY visitas:home 10     # contador atômico
$R SET sessao:abc123 '{"user_id": 2}' PX 1500                              # expira em 1,5 s (TTL)
echo "TTL (ms): $($R PTTL sessao:abc123)"; sleep 2
echo "depois de 2s: [$($R GET sessao:abc123)]"
$R HSET carrinho:2 PF-01 1 TC-02 3 >/dev/null; $R HGETALL carrinho:2        # hash (dicionário)
$R LPUSH fila:emails "pedido-20" "pedido-21" >/dev/null; $R RPOP fila:emails   # lista como fila simples
$R DEL produto:PF-01:preco visitas:home carrinho:2 fila:emails
```
```text
OK
89.90
1
2
12
OK
TTL (ms): 1447
depois de 2s: []
PF-01
1
TC-02
3
pedido-20
4
```
Redis guarda tudo em **memória** (rápido, mas limitado e, por padrão, volátil: pode persistir em disco, mas não é sua fonte da verdade). No MiniShop ele será usado para **cache** (Módulo 14), **fila de tarefas** com Celery (Módulo 7) e talvez *rate limiting* (Módulo 9). `INCR` é atômico (sem *lost update*).

**7. `jsonb` no PostgreSQL: a ponte entre relacional e documento**
```sql
ALTER TABLE products ADD COLUMN attributes jsonb NOT NULL DEFAULT '{}';
UPDATE products SET attributes = '{"cor": "preto", "conexao": "bluetooth", "garantia_meses": 12}' WHERE sku = 'AU-01';
UPDATE products SET attributes = '{"cor": "branco", "resolucao": "1080p"}' WHERE sku = 'PF-05';
CREATE INDEX products_attributes_gin ON products USING gin (attributes);

SELECT sku, name, attributes->>'cor' AS cor, (attributes->>'garantia_meses')::int AS garantia
FROM products WHERE attributes @> '{"cor": "preto"}';       -- @> : "contém" (usa o índice GIN)
SELECT sku, attributes FROM products WHERE attributes ? 'resolucao';
```
```text
  sku  |      name      |  cor  | garantia 
-------+----------------+-------+----------
 AU-01 | Fone Bluetooth | preto |       12
(1 row)

  sku  |               attributes                
-------+-----------------------------------------
 PF-05 | {"cor": "branco", "resolucao": "1080p"}
(1 row)
```
Use `jsonb` para atributos **variáveis e pouco consultados** (especificações técnicas); mantenha em colunas normais o que é central (preço, estoque, FKs): integridade e índices ficam melhores.

**8. MongoDB** (⚠️ descrito, **não executado** nesta aula): guarda documentos JSON em coleções, sem esquema fixo:
```javascript
db.produtos.insertOne({ sku: "AU-01", nome: "Fone", preco: 249.9, atributos: { cor: "preto", bluetooth: true } })
db.produtos.find({ "atributos.cor": "preto", preco: { $lt: 300 } }).sort({ preco: 1 })
```
Bom ajuste: catálogos com atributos muito diferentes, dados de eventos. Mau ajuste: dados altamente relacionais com regras entre entidades (pedidos × itens × estoque), que pedem transações, `JOIN` e constraints. Documentação: [MongoDB Manual](https://www.mongodb.com/docs/manual/).

## ⚠️ Erros comuns e boas práticas
| Mensagem / sintoma | Causa | Solução |
|---|---|---|
| Tela lenta com poucas linhas | N+1 consultas | `select_related`/`prefetch_related`; conte as consultas |
| Migração aplicada em dev e “sumiu” em produção | Migração editada depois de aplicada, ou não versionada | Nunca edite; crie outra; versione no Git |
| `column "x" does not exist` após deploy | Código novo antes da migração (ou o inverso) | Ordem: migrar primeiro e compatível com o código antigo |
| Remover coluna derruba a aplicação antiga | Rolling deploy com versões misturadas | Duas etapas: parar de usar, depois remover |
| Redis “perdeu” dados | Usado como banco principal sem persistência | Trate como cache/fila; a verdade fica no PostgreSQL |
| Escolher MongoDB “porque é mais moderno” | Moda, sem requisito | Comece pelo PostgreSQL; troque por evidência |
| ORM gerando SQL horrível | Consulta complexa demais | `.query` para inspecionar; SQL cru com parâmetros |

- **Veja o SQL** das consultas importantes (`str(qs.query)`, `EXPLAIN`).
- Esquema do banco é **código**: versionado, revisado em *pull request*, aplicado por ferramenta.
- Cada tecnologia nova é custo de operação, backup e conhecimento: adote com motivo.

## 🧠 Pausa para lógica
**Problema (cache com TTL).** Implemente `CacheTTL` em Python: `set(chave, valor, ttl)`, `get(chave)` que devolve `None` se expirou, e `limpar_expirados()`. Qual a complexidade de `get`/`set`? Por que o Redis usa a mesma ideia?

<details><summary>Dica</summary>
Um <code>dict</code> <code>chave → (valor, expira_em)</code> com <code>time.monotonic()</code>. <code>get</code> confere se já expirou e, se sim, apaga e devolve <code>None</code> (expiração preguiçosa).
</details>

<details><summary>Solução comentada</summary>

```python
import time

class CacheTTL:
    def __init__(self):
        self._dados = {}                               # tabela hash: O(1) em média

    def set(self, chave, valor, ttl):
        self._dados[chave] = (valor, time.monotonic() + ttl)

    def get(self, chave, padrao=None):
        item = self._dados.get(chave)
        if item is None:
            return padrao
        valor, expira_em = item
        if time.monotonic() >= expira_em:              # expiração "preguiçosa"
            del self._dados[chave]
            return padrao
        return valor

    def limpar_expirados(self):
        agora = time.monotonic()
        vencidos = [k for k, (_, e) in self._dados.items() if agora >= e]
        for k in vencidos:
            del self._dados[k]
        return len(vencidos)

c = CacheTTL()
c.set("preco:PF-01", "89.90", ttl=0.3)
c.set("preco:PF-02", "159.90", ttl=5)
print(c.get("preco:PF-01"), c.get("preco:PF-02"))
time.sleep(0.4)
print("expirados removidos pela limpeza:", c.limpar_expirados())
print(c.get("preco:PF-01"), c.get("preco:PF-02"))
```
```text
89.90 159.90
expirados removidos pela limpeza: 1
None 159.90
```
`get`/`set` são O(1) (hash); a limpeza total é O(n), por isso é feita de tempos em tempos. O Redis também combina expiração preguiçosa (ao acessar) com varredura periódica amostral. A **invalidação** (quando o dado muda antes do TTL) é a parte difícil de um cache: Módulo 14.
</details>

**Variação mais difícil:** limite o cache a `N` itens com política LRU (use `collections.OrderedDict`) e compare com `functools.lru_cache`.

## 🧩 Exercícios
**1. Fixação**
(a) Cite duas vantagens e duas desvantagens de um ORM. (b) Por que não se deve editar uma migração já aplicada? (c) Para cada dado do MiniShop, indique onde guardar: pedidos, sessão de login, cache do catálogo, fila de e-mails, especificações técnicas variáveis dos produtos.

<details><summary>Solução</summary>

(a) Vantagens: produtividade, parametrização por padrão, migrações; desvantagens: N+1, abstração que vaza/SQL opaco. (b) Outros ambientes já aplicaram a versão antiga; editar cria bancos diferentes sem registro da diferença: crie uma nova migração. (c) Pedidos: PostgreSQL (ACID); sessão: banco, cache ou Redis; cache do catálogo: Redis com TTL; fila de e-mails: Redis/RabbitMQ (Celery); especificações variáveis: coluna `jsonb`.
</details>

**2. Aplicação no projeto MiniShop**
Traga o schema do projeto para o regime de migrações.

Critérios de pronto:
- [ ] Pasta `projeto/sql/migracoes/` com `001_schema.sql` (o conteúdo de `loja.sql` sem os `INSERT`), `002_seed.sql` (dados de exemplo) e `003_reviews.sql` (a tabela `reviews` da aula 03 + índice na FK)
- [ ] `migrar.py` (do exemplo) aplicando as pendentes numa **base vazia** (`CREATE DATABASE loja_teste`) e deixando o banco idêntico ao `loja.sql`
- [ ] Rodar `migrar.py` duas vezes não altera nada (idempotente)
- [ ] Uma migração de “mudança segura”: adiciona `products.attributes jsonb` com padrão `'{}'` e índice GIN
- [ ] `docs/banco.md` explicando: por que migrações, como criar uma nova, e a regra “nunca editar uma aplicada”
- [ ] Commit `feat(db): move schema to versioned migrations`

<details><summary>Solução de referência</summary>

```bash
docker exec minishop-pg psql -U postgres -c "DROP DATABASE IF EXISTS loja_teste WITH (FORCE)" -c "CREATE DATABASE loja_teste"
# ajuste o DSN do migrar.py (variável de ambiente DATABASE_URL) para apontar para loja_teste, depois:
python migrar.py projeto/sql/migracoes
docker exec minishop-pg psql -U postgres -d loja_teste -c '\dt'
```
Para comparar os dois bancos: `pg_dump --schema-only` de cada um e `diff`.
</details>

**3. Desafio (opcional)**
Acrescente ao executor suporte a `-- down` (reversão): cada arquivo tem duas seções (`-- up` e `-- down`) e o comando `python migrar.py down 1` desfaz a última. Por que muitos times preferem “migrações só para frente”?

## 🎤 Na entrevista
- **O que é um ORM e quais os prós e contras?** Mapeia classes em tabelas e objetos em linhas, gerando SQL parametrizado e migrações; ganha produtividade e segurança, mas pode gerar N+1 e SQL ineficiente, e a abstração vaza (é preciso saber SQL).
- **O que é o problema N+1 e como resolver?** Uma consulta para a lista e uma adicional por item para um relacionamento; resolve-se com *join* (`select_related`) ou carregamento em lote (`prefetch_related`).
- **Para que servem migrações?** Versionar a evolução do schema, reproduzi-lo em qualquer ambiente e aplicá-lo de forma ordenada e automatizável, com registro do que já foi aplicado.
- **Quando usar Redis, MongoDB ou PostgreSQL?** PostgreSQL como fonte da verdade (relacional, transacional, com `jsonb` para flexibilidade); Redis para cache, contadores, sessões e filas; MongoDB quando o modelo é de documentos autocontidos com esquema muito variável e poucas relações.

## 📚 Para ir além
- 📄 Documentação oficial: [Django: consultas (QuerySet)](https://docs.djangoproject.com/en/5.2/topics/db/queries/). A API do ORM que você usará no Módulo 5.
- 📄 Documentação oficial: [Redis: documentação](https://redis.io/docs/latest/). Estruturas de dados e comandos.
- 📄 Documentação oficial: [MongoDB Manual](https://www.mongodb.com/docs/manual/). Modelo de documentos e consultas.
- 📄 Documentação oficial: [PostgreSQL: tipos JSON](https://www.postgresql.org/docs/current/datatype-json.html). `json` × `jsonb` e operadores.
- 🏋️ Prática extra: use `str(queryset.query)` em 5 consultas do ORM e traduza cada uma para o SQL que você escreveria à mão.

## ✅ Checklist da aula
- [ ] Rodei o mini-ORM e comparei com o ORM do Django
- [ ] Contei as consultas de um N+1
- [ ] Apliquei migrações com o executor e vi o rollback de uma migração quebrada
- [ ] Fiz comandos no Redis (TTL, contador atômico)
- [ ] Entreguei o schema como migrações
