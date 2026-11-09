# 09. Arquivos: txt, CSV e JSON

> ⏱️ ~1h30 · Módulo 1 · Pré-requisitos: [08](08-excecoes.md)

## 🎯 Objetivos
Ao final desta aula você consegue:
- Ler e escrever arquivos de texto com `with open(...)`
- Trabalhar com caminhos usando `pathlib`
- Ler e gravar CSV com `csv.DictReader`/`DictWriter`
- Serializar e carregar JSON (`json.dump`/`json.load`)
- Tratar erros de arquivo e problemas de codificação

## 🤔 Por que isso importa
Importar produtos de uma planilha CSV, guardar configurações, trocar dados com uma API em JSON: arquivos são a forma mais simples de persistir dados, e JSON é a língua das APIs (Módulos 2 e 6). Na CLI de estoque, o JSON será o “banco de dados” provisório.

## 💡 Intuição (explicação simples)
Abrir um arquivo é **pegar um caderno na estante**: você abre, lê ou escreve e **precisa devolver** (fechar), senão alguém fica sem o caderno. O `with` é o assistente que sempre devolve o caderno por você, mesmo se acontecer um problema no meio.

## 🔬 Como funciona por dentro
- `open(caminho, modo, encoding=...)` pede ao sistema operacional um **descritor de arquivo**. Modos: `"r"` ler, `"w"` escrever (apaga o que havia), `"a"` acrescentar, `"x"` criar (falha se existir); acrescente `"b"` para binário.
- O `with` é um **gerenciador de contexto**: ao sair do bloco, chama `close()` (aula 16).
- **Sempre** informe `encoding="utf-8"` para texto: o padrão varia por sistema e causa acentos quebrados.
- **CSV** é texto com colunas separadas por vírgula (ou `;` em planilhas brasileiras). **JSON** representa objetos (`{}`), listas (`[]`), texto, números, `true/false/null`.
- JSON ↔ Python: objeto↔`dict`, lista↔`list`, string↔`str`, número↔`int/float`, `true/false`↔`True/False`, `null`↔`None`. **Não** tem `Decimal`, `date` nem `set`: precisam de conversão.

## 🛠️ Exemplo prático
Os exemplos rodam em uma pasta temporária; no seu computador, use a pasta do projeto.

**1. Texto**
```python
from pathlib import Path

arq = Path("notas.txt")
with arq.open("w", encoding="utf-8") as f:
    f.write("linha 1\n")
    f.write("linha 2: coração\n")

with arq.open("a", encoding="utf-8") as f:
    f.write("linha 3\n")

with arq.open(encoding="utf-8") as f:
    for numero, linha in enumerate(f, start=1):      # lê linha a linha (não carrega tudo)
        print(numero, linha.rstrip())
print(arq.exists(), arq.stat().st_size, arq.suffix, arq.parent.resolve() == Path.cwd())
```
```text
1 linha 1
2 linha 2: coração
3 linha 3
True 35 .txt True
```

**2. CSV**
```python
import csv
from decimal import Decimal

produtos = [
    {"sku": "MS-01", "nome": "Mouse", "preco": "49.90", "qtd": "10"},
    {"sku": "TC-02", "nome": "Teclado", "preco": "120.00", "qtd": "4"},
]
with open("produtos.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["sku", "nome", "preco", "qtd"])
    w.writeheader()
    w.writerows(produtos)

print(open("produtos.csv", encoding="utf-8").read())
with open("produtos.csv", newline="", encoding="utf-8") as f:
    for linha in csv.DictReader(f):                   # cada linha vira dict; tudo é str!
        total = Decimal(linha["preco"]) * int(linha["qtd"])
        print(linha["nome"], total)
```
```text
sku,nome,preco,qtd
MS-01,Mouse,49.90,10
TC-02,Teclado,120.00,4

Mouse 499.00
Teclado 480.00
```
Tudo que vem do CSV é `str`: converta (`Decimal`, `int`) na leitura. Para CSV com `;`, use `csv.DictReader(f, delimiter=";")`.

**3. JSON**
```python
import json
from decimal import Decimal

estoque = {"MS-01": {"nome": "Mouse", "preco": Decimal("49.90"), "qtd": 10}}

def para_json(obj):
    if isinstance(obj, Decimal):
        return str(obj)                  # string preserva a precisão
    raise TypeError(f"tipo não serializável: {type(obj).__name__}")

with open("estoque.json", "w", encoding="utf-8") as f:
    json.dump(estoque, f, default=para_json, indent=2, ensure_ascii=False)

print(open("estoque.json", encoding="utf-8").read())
with open("estoque.json", encoding="utf-8") as f:
    dados = json.load(f)
print(dados["MS-01"]["preco"], type(dados["MS-01"]["preco"]).__name__)   # voltou como str
print(json.loads('{"ok": true, "x": null}'), json.dumps({"a": [1, 2]}))
```
```text
{
  "MS-01": {
    "nome": "Mouse",
    "preco": "49.90",
    "qtd": 10
  }
}
49.90 str
{'ok': True, 'x': None} {"a": [1, 2]}
```

**4. Erros de arquivo e JSON inválido**
```python
import json
for nome in ("nao_existe.json", "estoque.json"):
    try:
        with open(nome, encoding="utf-8") as f:
            print(nome, "lido:", list(json.load(f)))
    except FileNotFoundError:
        print(nome, "não encontrado")

try:
    json.loads("{'a': 1}")               # aspas simples não são JSON válido
except json.JSONDecodeError as e:
    print("JSON inválido:", e)
```
```text
nao_existe.json não encontrado
estoque.json lido: ['MS-01']
JSON inválido: Expecting property name enclosed in double quotes: line 1 column 2 (char 1)
```

## ⚠️ Erros comuns e boas práticas
| Mensagem | Causa | Solução |
|---|---|---|
| `FileNotFoundError: [Errno 2] No such file or directory` | Caminho errado ou pasta de execução diferente | Use `Path(__file__).parent / "arquivo"` e confira `Path.cwd()` |
| `UnicodeDecodeError: 'utf-8' codec can't decode byte ...` | Arquivo em outra codificação (ex.: Excel em `latin-1`/`cp1252`) | `encoding="latin-1"` ou peça o arquivo em UTF-8 |
| `json.decoder.JSONDecodeError: Expecting property name enclosed in double quotes` | JSON com aspas simples ou vírgula sobrando | Valide em um validador; JSON usa só aspas duplas |
| `TypeError: Object of type Decimal is not JSON serializable` | Tipo sem equivalente em JSON | `default=` como no exemplo |
| Linhas em branco entre registros no CSV (Windows) | Faltou `newline=""` | Sempre `open(..., newline="")` com `csv` |

- `"w"` **apaga** o arquivo existente sem avisar. Use `"x"` ou confira `exists()` quando for crítico.
- Para escrita segura, grave em arquivo temporário e renomeie (`Path.replace`), assim uma falha no meio não corrompe o original.
- Nunca carregue de uma vez (`.read()`) arquivos enormes; itere linha a linha.
- Nunca faça `eval()` em conteúdo de arquivo; use `json`.

## 🧠 Pausa para lógica
**Problema (importação).** Ao importar um CSV de produtos, algumas linhas têm preço inválido ou SKU repetido. Importe as válidas e devolva também a lista de erros com o número da linha.

<details><summary>Dica</summary>
Percorra com <code>enumerate(reader, start=2)</code> (a linha 1 é o cabeçalho). Um <code>set</code> de SKUs já vistos detecta repetição; um <code>try/except InvalidOperation</code> pega o preço ruim.
</details>

<details><summary>Solução comentada</summary>

```python
import csv, io
from decimal import Decimal, InvalidOperation

CSV = """sku,nome,preco,qtd
MS-01,Mouse,49.90,10
TC-02,Teclado,abc,4
MS-01,Mouse repetido,49.90,1
CB-03,Cabo,9.90,-5
MN-04,Monitor,899.00,2
"""

def importar(texto):
    ok, erros, vistos = [], [], set()
    for n, linha in enumerate(csv.DictReader(io.StringIO(texto)), start=2):
        try:
            preco = Decimal(linha["preco"])
            qtd = int(linha["qtd"])
        except (InvalidOperation, ValueError):
            erros.append((n, "preço ou quantidade inválidos"))
            continue
        if qtd < 0:
            erros.append((n, "quantidade negativa"))
        elif linha["sku"] in vistos:
            erros.append((n, "SKU repetido"))
        else:
            vistos.add(linha["sku"])
            ok.append({"sku": linha["sku"], "nome": linha["nome"], "preco": preco, "qtd": qtd})
    return ok, erros

ok, erros = importar(CSV)
print(len(ok), "válidos;", erros)
```
```text
2 válidos; [(3, 'preço ou quantidade inválidos'), (4, 'SKU repetido'), (5, 'quantidade negativa')]
```
</details>

**Variação mais difícil:** em vez de ignorar o SKU repetido, some as quantidades. O que muda na estrutura?

## 🧩 Exercícios
**1. Fixação**
Escreva um programa que lê `notas.txt` e imprime quantas linhas e quantas palavras tem (sem carregar o arquivo inteiro de uma vez).

<details><summary>Solução</summary>

```python
linhas = palavras = 0
with open("notas.txt", encoding="utf-8") as f:
    for linha in f:
        linhas += 1
        palavras += len(linha.split())
print(linhas, palavras)
```
```text
3 7
```
</details>

**2. Aplicação no projeto MiniShop**
Em `src/persistencia.py`, crie `salvar_estoque(caminho, estoque)` e `carregar_estoque(caminho)` em JSON (preços `Decimal` → string e de volta). Se o arquivo não existir, `carregar_estoque` devolve `{}`.

Critérios de pronto:
- [ ] Round-trip: o que se salva é igual ao que se carrega (inclusive `Decimal`)
- [ ] Arquivo inexistente não quebra
- [ ] JSON corrompido levanta uma exceção própria com mensagem clara
- [ ] `estoque.json` está no `.gitignore`
- [ ] Commit `feat: persist stock in json`

<details><summary>Solução de referência</summary>

```python
import json
from decimal import Decimal
from pathlib import Path

class EstoqueCorrompido(Exception):
    pass

def salvar_estoque(caminho, estoque):
    dados = {sku: {**p, "preco": str(p["preco"])} for sku, p in estoque.items()}
    tmp = Path(str(caminho) + ".tmp")
    tmp.write_text(json.dumps(dados, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(caminho)                       # troca atômica

def carregar_estoque(caminho):
    try:
        bruto = json.loads(Path(caminho).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError as e:
        raise EstoqueCorrompido(f"{caminho} está corrompido: {e}") from e
    return {sku: {**p, "preco": Decimal(p["preco"])} for sku, p in bruto.items()}

est = {"MS-01": {"nome": "Mouse", "preco": Decimal("49.90"), "qtd": 10}}
salvar_estoque("est2.json", est)
print(carregar_estoque("est2.json") == est, carregar_estoque("nada.json"))
```
```text
True {}
```
</details>

**3. Desafio (opcional)**
Exporte o estoque também para CSV e importe-o de volta, comparando com o JSON. Qual formato preserva melhor os tipos?

## 🎤 Na entrevista
- **Por que usar `with open(...)`?** Garante o fechamento do arquivo mesmo se ocorrer exceção.
- **Diferença entre `json.load` e `json.loads`?** `load` lê de um arquivo; `loads` lê de uma string (o “s” é de *string*). O mesmo vale para `dump`/`dumps`.
- **Por que informar `encoding="utf-8"`?** O padrão depende do sistema operacional; sem ele, acentos podem corromper em outra máquina.

## 📚 Para ir além
- 📄 Documentação oficial: [Tutorial: leitura e escrita de arquivos](https://docs.python.org/3/tutorial/inputoutput.html#reading-and-writing-files). Modos, `with` e JSON.
- 📄 Documentação oficial: [`csv`](https://docs.python.org/3/library/csv.html) e [`json`](https://docs.python.org/3/library/json.html). Referências com exemplos.
- 📄 Documentação oficial: [`pathlib`](https://docs.python.org/3/library/pathlib.html). Caminhos como objetos.
- 🏋️ Prática extra: baixe qualquer CSV público pequeno e some uma coluna numérica.

## ✅ Checklist da aula
- [ ] Usei `with open(..., encoding="utf-8")` em todos os exemplos
- [ ] Fiz o round-trip de `Decimal` em JSON
- [ ] Tratei arquivo inexistente e JSON inválido
- [ ] Fiz o commit do exercício
