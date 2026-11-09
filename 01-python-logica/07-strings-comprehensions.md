# 07. Strings, f-strings e comprehensions

> ⏱️ ~1h30 · Módulo 1 · Pré-requisitos: [06](06-dicts-sets.md)

## 🎯 Objetivos
Ao final desta aula você consegue:
- Manipular texto com fatias e métodos (`strip`, `split`, `join`, `replace`, `lower`)
- Formatar saídas com f-strings (alinhamento, casas decimais)
- Escrever list, dict e set comprehensions e expressões geradoras
- Decidir quando uma comprehension fica ilegível
- Validar texto (CPF, senha forte) com laços e condicionais

## 🤔 Por que isso importa
Formulários, CSVs, URLs, logs e JSON são texto. Limpar entrada do usuário e montar mensagens é diário. Comprehensions são o jeito idiomático de transformar listas e aparecem em todo código Python profissional.

## 💡 Intuição (explicação simples)
- **String** = um **colar de contas (caracteres)** que não pode ser alterado: para mudar uma conta você faz outro colar.
- **Comprehension** = uma **linha de montagem escrita em uma frase**: “para cada produto, se estiver ativo, pegue o nome em maiúsculas”.

## 🔬 Como funciona por dentro
- `str` é uma sequência **imutável** de caracteres Unicode: indexação e fatias funcionam como em listas; métodos como `upper()` **devolvem** uma string nova.
- `"a" + "b"` em laço cria muitas strings intermediárias; para juntar muitas, use `", ".join(lista)`.
- f-string: `f"{valor:formato}"` avalia expressões dentro de `{}`; o formato segue `[alinhamento][largura][.casas][tipo]`.
- Comprehension: `[expr for x in iteravel if cond]`. Equivale a um laço que cria uma lista, mas mais curto e geralmente mais rápido. A versão com `()` é uma **expressão geradora**: não cria a lista inteira, produz item a item (aula 15).

## 🛠️ Exemplo prático
**1. Métodos de string**
```python
s = "  Teclado Mecânico RGB  "
print(repr(s.strip()), s.lower().strip(), s.strip().split())
print("-".join(["a", "b", "c"]), "banana".replace("a", "o"), "banana".count("a"))
print("Teclado".startswith("Tec"), "ão" in "coração", "abc"[::-1], len("coração"))
```
```text
'Teclado Mecânico RGB' teclado mecânico rgb ['Teclado', 'Mecânico', 'RGB']
a-b-c bonono 3
True True cba 7
```

**2. f-strings**
```python
nome, preco, qtd = "Mouse", 49.9, 3
print(f"{nome:<10}|{qtd:>4}|{preco:>8.2f}|{preco * qtd:>9,.2f}")
print(f"{0.256:.1%}  {1234567:,}  {42:05d}  {nome!r}  {preco=}")
```
```text
Mouse     |   3|   49.90|   149.70
25.6%  1,234,567  00042  'Mouse'  preco=49.9
```

**3. Comprehensions**
```python
precos = [50, 120, 900, 35]
print([p * 2 for p in precos])
print([p for p in precos if p > 100])
print({p: p > 100 for p in precos})
print({len(w) for w in ["a", "bb", "cc"]})
produtos = [{"nome": "Mouse", "ativo": True}, {"nome": "Cabo", "ativo": False}]
print([p["nome"].upper() for p in produtos if p["ativo"]])
print(sum(p for p in precos if p > 100))     # expressão geradora, sem criar lista
```
```text
[100, 240, 1800, 70]
[120, 900]
{50: False, 120: True, 900: True, 35: False}
{1, 2}
['MOUSE']
1020
```

**4. Quando NÃO usar comprehension**
```python
# legível: uma transformação e um filtro
nomes = [p["nome"] for p in produtos if p["ativo"]]
# ilegível: aninhada com várias condições -> prefira um laço
resultado = []
for p in produtos:
    if p["ativo"]:
        resultado.append(p["nome"].strip().lower())
print(nomes, resultado)
```
```text
['Mouse'] ['mouse']
```

## ⚠️ Erros comuns e boas práticas
| Mensagem | Causa | Solução |
|---|---|---|
| `TypeError: 'str' object does not support item assignment` | `s[0] = "x"` | Strings são imutáveis: `s = "x" + s[1:]` |
| `SyntaxError: f-string: expecting '}'` | Chave/aspa mal fechada na f-string | Confira `{}` e as aspas internas |
| `ValueError: Unknown format code 'f' for object of type 'str'` | `:.2f` aplicado a texto | Converta para número antes |
| Acentos “quebrados” (`CafÃ©`) | Arquivo lido com codificação errada | Abra com `encoding="utf-8"` (aula 09) |

- Nunca monte SQL com f-string a partir da entrada do usuário (SQL injection; Módulo 3).
- Para texto longo, `"".join(partes)` é melhor que `+=` em laço.
- Comprehension com mais de ~2 cláusulas deve virar laço.

## 🧠 Pausa para lógica
**Problema (CPF).** Valide um CPF: 11 dígitos (aceite pontos e traço), não todos iguais, e com os dois dígitos verificadores corretos. O 1º dígito: multiplique os 9 primeiros por 10, 9, …, 2, some, `resto = (soma * 10) % 11`, e se `resto == 10` vale 0. O 2º: use os 10 primeiros com pesos 11…2.

<details><summary>Dica</summary>
Primeiro limpe: <code>"".join(c for c in cpf if c.isdigit())</code>. Crie uma função auxiliar <code>digito(base, peso_inicial)</code> que serve para os dois dígitos.
</details>

<details><summary>Solução comentada</summary>

```python
def cpf_valido(cpf: str) -> bool:
    d = [int(c) for c in cpf if c.isdigit()]
    if len(d) != 11 or len(set(d)) == 1:       # tamanho e "todos iguais"
        return False

    def digito(base, peso_inicial):
        soma = sum(n * p for n, p in zip(base, range(peso_inicial, 1, -1)))
        r = (soma * 10) % 11
        return 0 if r == 10 else r

    return d[9] == digito(d[:9], 10) and d[10] == digito(d[:10], 11)

for c in ("529.982.247-25", "111.111.111-11", "529.982.247-24", "123"):
    print(c, cpf_valido(c))
```
```text
529.982.247-25 True
111.111.111-11 False
529.982.247-24 False
123 False
```
O CPF de exemplo `529.982.247-25` é um número de teste usado na documentação de validadores, não pertence a ninguém conhecido. **Nunca** use CPFs reais em exemplos ou testes.
</details>

**Variação mais difícil:** valide uma **senha forte** (≥ 10 caracteres, maiúscula, minúscula, dígito e símbolo) e devolva a lista de requisitos que faltam.

## 🧩 Exercícios
**1. Fixação**
Dada `frase = "  o rato roeu a roupa  "`, produza: (a) frase limpa com cada palavra capitalizada, (b) a palavra mais longa, (c) quantas vezes a letra `r` aparece.

<details><summary>Solução</summary>

```python
frase = "  o rato roeu a roupa  "
print(frase.strip().title())
print(max(frase.split(), key=len))
print(frase.count("r"))
```
```text
O Rato Roeu A Roupa
roupa
3
```
</details>

**2. Aplicação no projeto MiniShop**
Em `src/texto.py`, crie `slugify(nome)` (ex.: `"Teclado Mecânico RGB"` → `"teclado-mecanico-rgb"`) e `normalizar_busca(termo)`. O slug será usado nas URLs do catálogo.

Critérios de pronto:
- [ ] Remove acentos (use `unicodedata.normalize("NFKD", ...)`)
- [ ] Só letras minúsculas, números e hífens, sem hífens duplicados ou nas pontas
- [ ] Testado com 4 entradas, incluindo vazia e só símbolos
- [ ] Commit `feat: add slugify helper`

<details><summary>Solução de referência</summary>

```python
import re
import unicodedata

def slugify(nome: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-z0-9]+", "-", sem_acento.lower())
    return slug.strip("-")

for t in ("Teclado Mecânico RGB", "  Café & Pão!  ", "", "@@@"):
    print(repr(t), "->", repr(slugify(t)))
```
```text
'Teclado Mecânico RGB' -> 'teclado-mecanico-rgb'
'  Café & Pão!  ' -> 'cafe-pao'
'' -> ''
'@@@' -> ''
```
</details>

**3. Desafio (opcional)**
Reescreva `slugify` sem `re`, só com laço e `isalnum()`. Compare legibilidade.

## 🎤 Na entrevista
- **Strings são mutáveis?** Não; métodos devolvem novas strings. Para muitas concatenações, use `join`.
- **O que é uma list comprehension e quando evitar?** Sintaxe compacta para criar listas a partir de iteráveis; evite quando houver lógica aninhada que prejudique a leitura.
- **Diferença entre `[x for ...]` e `(x for ...)`?** A primeira cria a lista toda na memória; a segunda é um gerador, produz sob demanda.

## 📚 Para ir além
- 📄 Documentação oficial: [Métodos de string](https://docs.python.org/3/library/stdtypes.html#string-methods). Referência completa.
- 📄 Documentação oficial: [Mini-linguagem de formatação](https://docs.python.org/3/library/string.html#format-specification-mini-language). Todos os formatos de f-string.
- 📄 Documentação oficial: [List comprehensions](https://docs.python.org/3/tutorial/datastructures.html#list-comprehensions). Sintaxe e aninhamento.
- 🏋️ Prática extra: valide senhas fortes e liste o que falta.

## ✅ Checklist da aula
- [ ] Formatei uma tabela alinhada com f-strings
- [ ] Reescrevi um laço como comprehension (e o contrário)
- [ ] Validei o CPF de teste
- [ ] Fiz o commit do exercício
