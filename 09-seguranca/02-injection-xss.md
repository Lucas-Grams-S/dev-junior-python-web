# 2. Injeção de SQL e XSS: reconhecer, corrigir e travar

> ⏱️ ~1h30 · Módulo 9 · Pré-requisitos: [9.01](01-owasp-ameacas.md), [8.07 (a injeção de SQL do legado)](../08-arquitetura/07-legado-refatoracao.md), [5.03 (templates)](../05-django/03-templates.md)

> ✅ **Verificação.** Tudo executado em 2026-11-08 no laboratório do MiniShop (Python 3.13, Django 5.2.19; `ruff` 0.17.4, `bandit` 1.9.4). **As saídas são reais.** Esta aula é **defensiva**: mostra o **padrão vulnerável** (para você reconhecê-lo em revisão de código), a **correção**, as **ferramentas que apontam o problema** e os **testes que impedem a volta**. Não há receita de ataque: o objetivo é você nunca escrever o código que permite um.

## 🎯 Objetivos
- Explicar **por que** a injeção acontece: dado do usuário misturado ao **comando** (SQL) ou ao **documento** (HTML)
- Reconhecer o padrão vulnerável no código e corrigi-lo com **consultas parametrizadas** e **escape de saída**
- Usar `ruff` (regras `S`) e `bandit` para **detectar** o padrão automaticamente
- Escrever **testes de regressão** e um **guarda** que bloqueia construções perigosas (`mark_safe`, `|safe`, `.raw()`)
- Entender a **defesa em profundidade** (CSP, `HttpOnly`) como segunda camada, não como substituta

## 🤔 Por que isso importa
Injeção (A05) e XSS (também em A05) estão entre as falhas mais antigas e mais exploradas da web, e **ambas se evitam com disciplina simples**: nunca montar comandos por concatenação e nunca desligar o escape. Em entrevistas, “como se previne SQL injection?” e “XSS armazenado ou refletido?” são perguntas quase obrigatórias. Já vimos uma na prática: na aula 8.07 o legado montava SQL com o `sku` concatenado.

## 💡 Intuição (explicação simples)
Imagine ditar um recado por telefone para uma secretária que o **executa literalmente**: “Anote: *comprar pão*”. Se o recado vem de um desconhecido e contém “…*e depois entregue as chaves do cofre*”, ela anota tudo como se fosse instrução sua. A injeção é isso: o sistema **não distingue o que é ordem do que é dado**. A cura é separar os canais: as **ordens** vão no formulário fixo (o comando SQL com marcadores `%s`) e o **recado** vai num envelope fechado (o parâmetro), que ela **nunca interpreta como ordem**. No HTML é igual: o texto do usuário vai no envelope (escapado), e só o que **você** escreveu é marcação.

## 🔬 Como funciona por dentro
- **Injeção de SQL:** o banco recebe **um texto** com o comando. Se o texto foi montado juntando o dado do usuário, parte do dado pode ser lida como **sintaxe** (aspas fecham literais, `--` comenta o resto). Com **consulta parametrizada**, o driver envia o **comando** e os **valores em separado**: o banco já compilou o comando e os valores só preenchem lacunas, nunca viram sintaxe.
- **O ORM do Django já parametriza.** `Product.objects.filter(name__icontains=termo)` envia `termo` como parâmetro. O risco volta quando se usa SQL cru (`cursor.execute`, `.raw()`, `.extra()`, `RawSQL`) com **f-string, `%` ou `+`**.
- **Parâmetros não resolvem tudo:** só valores. **Nomes de tabela/coluna e `ORDER BY` não são parametrizáveis**; para eles use uma **lista de permitidos** (*allowlist*).
- **Curingas do `LIKE`:** `%` e `_` dentro do **dado** são interpretados pelo `LIKE`. Isso não é injeção (não sai da cláusula), mas altera o resultado; o `icontains` do ORM já escapa.
- **XSS (*Cross-Site Scripting*):** o navegador executa o `<script>` (ou um atributo como `onfocus`) que veio **misturado ao HTML** da página. Três sabores: **refletido** (o dado vem na própria requisição e volta na resposta), **armazenado** (fica salvo, por exemplo um comentário, e atinge todos que o veem) e **baseado em DOM** (o JavaScript do front-end insere o dado como HTML). O impacto: o atacante age **como o usuário** na sua sessão.
- **A defesa é o *escape de saída* conforme o contexto**: texto HTML, atributo, URL, JavaScript e CSS têm regras diferentes. O motor de templates do Django faz o *autoescape* de HTML por padrão; ele **não** protege contexto de JavaScript ou URLs montadas à mão (`href="javascript:..."`).
- **Duas camadas extras (defesa em profundidade):** **CSP** (*Content-Security-Policy*) limita de onde scripts podem rodar (aula 06); **cookie `HttpOnly`** impede que scripts leiam o cookie de sessão. Elas **reduzem o dano**, não substituem o escape.
- **APIs JSON:** a resposta `application/json` com `X-Content-Type-Options: nosniff` não é interpretada como HTML pelo navegador. O XSS acontece quando o **front-end** pega o JSON e o insere com `innerHTML`: use `textContent` ou um framework que escapa (aula 4).

## 🛠️ Exemplo prático
**1. O padrão vulnerável e as duas formas corretas** (`seclab/consultas.py`: o anti-padrão existe **só** para as ferramentas apontarem; nenhuma rota o usa)
```python
"""Duas versões da MESMA busca por nome. A primeira é o ANTI-PADRÃO (existe só para as ferramentas apontarem); nunca é roteada."""
from django.db import connection

from apps.catalog.models import Product


def buscar_vulneravel(termo):
    # ANTI-PADRÃO: o texto do usuário vira parte do comando SQL.
    sql = f"SELECT sku, name FROM catalog_product WHERE is_active = 1 AND name LIKE '%{termo}%'"
    with connection.cursor() as c:
        c.execute(sql)
        return c.fetchall()


def _escapa_like(termo):
    return termo.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def buscar_segura(termo):
    # ORM: o valor viaja como PARÂMETRO, separado do comando.
    return list(Product.objects.filter(is_active=True, name__icontains=termo).values_list("sku", "name"))


def buscar_segura_sql_cru(termo):
    # SQL cru: marcadores %s e lista de parâmetros (nunca f-string). Portável: TRUE (não 1) e LOWER() dos dois lados, pois o LIKE do PostgreSQL distingue maiúsculas.
    with connection.cursor() as c:
        c.execute("SELECT sku, name FROM catalog_product WHERE is_active = TRUE AND LOWER(name) LIKE LOWER(%s) ESCAPE '\\'", [f"%{_escapa_like(termo)}%"])
        return c.fetchall()
```
> 🔎 **Portabilidade do SQL cru.** Ao rodar a suíte no PostgreSQL, a versão parametrizada falhou por duas diferenças que o SQLite escondia: `is_active = 1` (o PostgreSQL não compara booleano com inteiro: use `TRUE`) e o `LIKE` (no PostgreSQL ele **distingue maiúsculas**; compare `LOWER(coluna) LIKE LOWER(%s)`). Mais um motivo para preferir o ORM e para rodar os testes no banco de produção.

Repare na diferença de uma linha: no vulnerável, o `termo` vira **parte do texto SQL** (`f"...'%{termo}%'"`); nos seguros, ele só aparece na **lista de parâmetros**.

**2. As ferramentas apontam o padrão sozinhas** (sem executar nada):
```bash
uv run ruff check --isolated --select S608 seclab/consultas.py
uv run bandit -q seclab/consultas.py
```
```text
seclab/consultas.py:9:11: S608 Possible SQL injection vector through string-based query construction

>> Issue: [B608:hardcoded_sql_expressions] Possible SQL injection vector through string-based query construction.
   Severity: Medium   Confidence: Low
   CWE: CWE-89
   Location: ./seclab/consultas.py:9:12
```
Note `Confidence: Low`: a ferramenta sinaliza **o padrão** (SQL montado por texto), sem saber se o valor vem do usuário. Por isso o achado exige **revisão humana**, e por isso o CI deve rodar as regras sem ignorá-las em massa.

**3. Testes que travam a correção** (`tests/test_sqli_defesa.py`). A versão segura precisa tratar entradas “estranhas” como **texto comum**: aspas, comentários SQL, o curinga `%` e o apóstrofo legítimo de um nome (“O'Brien”):
```python
class TestBuscaSegura:
    def test_apostrofo_e_texto_comum(self, produtos, buscar):
        assert [s for s, _ in buscar("O'Brien")] == ["A-2"]

    def test_entrada_com_aspas_e_comentario_nao_muda_a_consulta(self, produtos, buscar):
        assert buscar("x' OR '1'='1") == []                  # é só um texto que ninguém tem no nome
        assert buscar("'; --") == []

    def test_nunca_devolve_inativos(self, produtos, buscar):
        assert buscar("oculto") == []

    def test_busca_normal_continua_funcionando(self, produtos, buscar):
        assert [s for s, _ in buscar("caneta")] == ["A-1"]


def test_curinga_percent_e_literal_na_versao_com_escape(produtos):
    assert [s for s, _ in buscar_segura_sql_cru("100%")] == ["A-3"]
    assert buscar_segura_sql_cru("%") == [("A-3", "Cola 100% branca")]     # só quem tem '%' no nome
```
```bash
uv run pytest -q tests/test_sqli_defesa.py
```
```text
9 passed
```
O mesmo conjunto roda contra **as duas** implementações seguras (ORM e SQL cru parametrizado). Um nome com apóstrofo, que **quebrava** a busca na versão antiga do legado (aula 8.07), agora é só um nome.

**4. XSS: o escape de saída do Django, em quatro contextos** (`xss_escape.py`; o texto de entrada é um comentário que contém marcação HTML)
```python
"""Escape de saída no Django: o mesmo texto, em três situações. O valor é só um comentário com marcação HTML."""
import os, sys
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
sys.path.insert(0, os.environ["LAB"])
import django
django.setup()
from django.template import engines
from django.utils.html import format_html
from django.utils.safestring import mark_safe

django_t = engines["django"]
comentario = 'Ótimo! <b>negrito</b> & "aspas" <script>alert(1)</script>'

def render(src, **ctx):
    return django_t.from_string(src).render(ctx)

print("1) autoescape (padrão):            ", render("<p>{{ c }}</p>", c=comentario))
print("2) com |safe (DESLIGA a proteção):  ", render("<p>{{ c|safe }}</p>", c=comentario))
print("3) em atributo, entre aspas:        ", render('<input value="{{ c }}">', c='" onfocus="x'))
print("4) format_html escapa os argumentos:", format_html("<a href='/u/{}'>{}</a>", "a&b", "<i>x</i>"))
print("5) mark_safe confia no que você passa:", mark_safe(comentario)[:34] + "...")
print("6) json_script (dados para o JS):   ", render("{% load static %}{{ d|json_script:'dados' }}", d={"texto": "</script><b>"}))
```
```text
1) autoescape (padrão):             <p>Ótimo! &lt;b&gt;negrito&lt;/b&gt; &amp; &quot;aspas&quot; &lt;script&gt;alert(1)&lt;/script&gt;</p>
2) com |safe (DESLIGA a proteção):   <p>Ótimo! <b>negrito</b> & "aspas" <script>alert(1)</script></p>
3) em atributo, entre aspas:         <input value="&quot; onfocus=&quot;x">
4) format_html escapa os argumentos: <a href='/u/a&amp;b'>&lt;i&gt;x&lt;/i&gt;</a>
5) mark_safe confia no que você passa: Ótimo! <b>negrito</b> & "aspas" <s...
6) json_script (dados para o JS):    <script id="dados" type="application/json">{"texto": "\u003C/script\u003E\u003Cb\u003E"}</script>
```
Como ler:
1. **Autoescape (padrão):** `<` vira `&lt;`, `&` vira `&amp;`, aspas viram `&quot;`: o navegador mostra o texto, **não** interpreta a marcação.
2. **`|safe`:** diz ao Django “este texto já é HTML confiável”. O escape some. Só use com HTML **que você mesmo gerou** (ou já sanitizado por uma biblioteca de sanitização), nunca com conteúdo de usuário.
3. **Atributo entre aspas:** as aspas do dado foram escapadas (`&quot;`), então não dá para “fechar” o atributo. **Sem aspas** no atributo, o escape não bastaria: sempre use aspas.
4. **`format_html`:** escapa os **argumentos** e confia só no seu modelo; é a forma correta de montar HTML em Python.
5. **`mark_safe`:** faz o mesmo que `|safe`, em Python. É uma promessa sua ao framework.
6. **`json_script`:** para passar dados ao JavaScript sem concatenar em `<script>`; ele escapa até o `</script>` (`</script>`).

**5. Travando a regressão** (`tests/test_pontos_perigosos.py`): um guarda que **falha** se alguém introduzir `mark_safe`, `|safe`, `autoescape off`, `.raw()`/`.extra()` ou `csrf_exempt` sem registrar uma exceção justificada. A única exceção atual é o webhook (autenticado por assinatura HMAC, aula 7.09):
```python
    "filtro |safe": r"\|\s*safe\b",
    "autoescape off": r"autoescape\s+off",
    "csrf_exempt": r"\bcsrf_exempt\b",
}
# Exceções JUSTIFICADAS (arquivo -> padrão): o webhook é autenticado por assinatura HMAC, não por cookie (aula 7.09).
PERMITIDO = {("apps/payments/api.py", "csrf_exempt")}


def arquivos():
    for pasta in ("apps", "config"):
        for p in (RAIZ / pasta).rglob("*"):
```
Validei o guarda por **mutação**: ao criar um arquivo com `mark_safe`, o teste **falhou** apontando a linha exata; ao removê-lo, voltou a passar:
```text
E         apps/catalog/zz_tmp.py:2: X = mark_safe("<b>")
FAILED tests/test_pontos_perigosos.py::test_sem_construcao_perigosa[mark_safe-...]
(arquivo removido) 7 passed
```

**6. Varredura do código do MiniShop** (`ruff` regras `S` e `bandit`, excluindo o anti-padrão de demonstração):
```text
== ruff (regras S, as do bandit) no código do MiniShop, sem tests/seclab/migrations/legado:
All checks passed!
== bandit (todas as severidades) em apps e config:
```
Na primeira rodada as duas ferramentas apontaram **um** achado: o valor fixo da `SECRET_KEY` usado em desenvolvimento (`B105`/`S105`, severidade baixa). Corrigi gerando uma chave aleatória **por processo** quando `DEBUG=1` (sem literal no código). Depois: `ruff` limpo e `bandit` sem achados. Suíte do laboratório: **162 passed, 1 skipped**.

**7. O que cada camada protege**
| Ameaça | Camada principal | Camada extra |
|---|---|---|
| SQL injection | consulta parametrizada / ORM | menor privilégio no banco (aula 07), `ruff S608` no CI |
| XSS armazenado/refletido | autoescape / `format_html` | CSP (aula 06), cookie `HttpOnly` |
| XSS por `innerHTML` no front | `textContent` / framework | CSP |
| Injeção em comando do SO (`subprocess`) | lista de argumentos, sem `shell=True` | `bandit B602`/`S602` |

## 🧠 Pausa para lógica
**Problema.** Uma tela de relatório deixa o usuário ordenar por uma coluna escolhida num `<select>`, e o código faz `qs.order_by(request.GET["col"])` e, em outro relatório, `cursor.execute(f"SELECT ... ORDER BY {col}")`. (a) Os parâmetros `%s` resolveriam o segundo caso? (b) O que fazer? (c) E o `order_by` do ORM é seguro?

<details><summary>Dica</summary>Parâmetros substituem <em>valores</em>, não <em>identificadores</em> (nomes de coluna).</details>

<details><summary>Solução comentada</summary>

(a) **Não.** `ORDER BY %s` com parâmetro ordenaria por uma **constante** (o texto), ou o driver recusaria; identificadores não são parametrizáveis. (b) Use uma ***allowlist***: `COLUNAS = {"nome": "name", "preco": "price"}` e `col = COLUNAS.get(pedido, "name")`: o texto do usuário nunca entra no SQL, só uma chave que **você** mapeia. (c) O ORM **valida** o nome contra os campos do modelo e levanta `FieldError` se não existir, mas ainda permite ordenar por **campos que você não queria expor** (ex.: `user__password`, via relações). Por isso, mesmo no ORM, restrinja a uma lista (como a aula 6 fez com a ordenação “fora da lista é ignorada”).
</details>

## ⚠️ Erros comuns e boas práticas
| Sintoma | Causa | Solução |
|---|---|---|
| `cursor.execute(f"... {x} ...")` | Montar SQL por texto | `execute(sql, [x])` ou ORM |
| “Escapei as aspas na mão” | `replace("'", "''")` é frágil e dependente do banco | Parâmetros, sempre |
| `ORDER BY`/tabela vinda do usuário | Identificadores não parametrizam | *Allowlist* |
| `\|safe` em conteúdo de usuário | Querer “aceitar HTML” | Sanitizar com biblioteca dedicada ou aceitar só texto/Markdown |
| `mark_safe(f"<b>{nome}</b>")` | Concatena dado em HTML “seguro” | `format_html("<b>{}</b>", nome)` |
| Dado em `<script>var x = "{{ d }}"</script>` | Contexto JavaScript sem escape adequado | `json_script` |
| `element.innerHTML = dadoDaApi` | XSS no front | `textContent` |
| `href="{{ url_do_usuario }}"` | Esquema `javascript:` | Validar o esquema (`http`/`https`) |
| Achado do `bandit` ignorado em massa (`# nosec` por tudo) | Ruído | Revisar cada um; registrar exceções justificadas |
| Confiar só na CSP | Achar que bloqueia tudo | CSP é camada extra; o escape é a defesa |

- **Valide na entrada, escape na saída.** Validar (tipo, tamanho, formato) reduz a superfície; **escapar conforme o contexto** é o que impede a injeção.
- **Menor privilégio no banco** (aula 07): a conta da aplicação não deveria poder apagar tabelas.
- **Ferramentas no CI**: `ruff` com regras `S`, `bandit`, e o guarda de construções perigosas.

## 🧩 Exercícios
**1. Fixação.** (a) Por que uma consulta parametrizada impede a injeção? (b) Cite três contextos de saída com regras de escape diferentes. (c) Diferencie XSS refletido, armazenado e baseado em DOM. (d) Por que a CSP não substitui o escape?

<details><summary>Solução</summary>

(a) O comando e os valores seguem separados; o banco já interpretou o comando, e os valores só preenchem lacunas. (b) HTML (texto), atributo HTML, URL, JavaScript, CSS. (c) Refletido: o dado volta na resposta da mesma requisição; armazenado: fica salvo e atinge quem visualizar; DOM: o JavaScript do cliente insere o dado como HTML. (d) A CSP é uma política de execução que pode ter brechas ou estar mal configurada; é uma segunda camada que reduz o dano, mas a falha continua no código.
</details>

**2. Aplicação no projeto MiniShop.**
- [ ] Revisão de todo SQL cru do projeto (`grep` por `execute`, `.raw(`, `.extra(`) com a lista de ocorrências e a decisão sobre cada uma
- [ ] Busca e ordenação com **allowlist** de campos
- [ ] `ruff` (regras `S`) e `bandit` no CI, sem achados ou com exceções **justificadas por escrito**
- [ ] `tests/test_sqli_defesa.py` (entradas estranhas viram texto) e o guarda de construções perigosas
- [ ] Validação por **mutação** do guarda (introduza o problema, veja o teste falhar, reverta)
- [ ] Seção “Injeção e XSS” em `docs/seguranca.md` com antes/depois
- [ ] Commit `fix(security): parametrized queries and dangerous-construct guard`

**3. Desafio (opcional).** Escreva um teste que percorra **todas** as rotas de listagem da API com um termo de busca cheio de aspas e símbolos e garanta que a resposta é sempre `200` ou `400`, nunca `500`.

## 🎤 Na entrevista
- **Como se previne SQL injection?** Consultas parametrizadas (ou ORM), nunca concatenar dado do usuário no SQL; *allowlist* para nomes de coluna/tabela; menor privilégio na conta do banco; validação de entrada como camada extra.
- **O ORM do Django protege contra SQL injection?** Sim, ele parametriza; o risco volta com `raw()`, `extra()`, `RawSQL` e `cursor.execute` montados por texto.
- **Qual a diferença entre XSS armazenado, refletido e baseado em DOM?** Armazenado: persiste e atinge quem vê; refletido: vem na requisição e volta na resposta; DOM: o JavaScript do cliente insere o dado como HTML.
- **Como evitar XSS?** Escape de saída conforme o contexto (o Django faz *autoescape* de HTML), evitar `|safe`/`mark_safe`/`innerHTML` com dado de usuário, CSP e cookies `HttpOnly` como camadas extras.
- **O que é defesa em profundidade?** Várias camadas independentes (validação, escape, CSP, privilégios mínimos), de modo que uma falha não seja fatal.

## 📚 Para ir além
- 📄 Guia: [OWASP — SQL Injection Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html). Defesas em ordem de preferência (em inglês).
- 📄 Guia: [OWASP — XSS Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html). Escape por contexto (em inglês).
- 📄 Documentação oficial: [Django — Templates (autoescape)](https://docs.djangoproject.com/en/5.2/ref/templates/language/). Como funciona o escape automático.
- 📄 Documentação oficial: [Django — Filtros e tags (`safe`, `json_script`)](https://docs.djangoproject.com/en/5.2/ref/templates/builtins/). O que cada um faz.
- 📄 Documentação oficial: [Django — SQL cru](https://docs.djangoproject.com/en/5.2/topics/db/sql/). Como passar parâmetros.
- 📄 Documentação oficial: [Django — Segurança](https://docs.djangoproject.com/en/5.2/topics/security/). Injeção e XSS no framework.
- 📄 Documentação: [Bandit](https://bandit.readthedocs.io/en/latest/). Verificações de segurança para Python.
- 📄 Documentação: [Regras `S` do ruff](https://docs.astral.sh/ruff/rules/#flake8-bandit-s). O mesmo conjunto, no linter.
- 📑 Verbete: [CWE-89 (SQL Injection)](https://cwe.mitre.org/data/definitions/89.html) e [CWE-79 (XSS)](https://cwe.mitre.org/data/definitions/79.html). Catálogo de fraquezas (em inglês).

## ✅ Checklist da aula
- [ ] Sei explicar por que parâmetros impedem a injeção e o que eles **não** cobrem
- [ ] Reconheço `f"...{x}..."` em SQL e `|safe`/`mark_safe` em revisão de código
- [ ] Rodei `ruff S` e `bandit` e entendi cada achado
- [ ] Tenho testes de regressão e um guarda validado por mutação
- [ ] Sei por que CSP e `HttpOnly` são camadas extras, não substitutas
