# 04. JavaScript essencial: tipos e funções

> ⏱️ ~1h30 · Módulo 4 · Pré-requisitos: [Módulo 1](../01-python-logica/README.md) (variáveis, funções, estruturas), [aula 3.10](../03-banco-de-dados/10-psycopg-sql-injection.md) (JSON)

## 🎯 Objetivos
Ao final desta aula você consegue:
- Declarar variáveis com `const`/`let` e explicar por que se evita `var`
- Reconhecer os tipos do JavaScript e suas pegadinhas (`typeof null`, `NaN`, `==` × `===`, *truthy*/*falsy*)
- Manipular arrays e objetos com `map`, `filter`, `reduce`, desestruturação e *spread*
- Escrever funções (declaração, expressão e *arrow*) e explicar **closures**
- Tratar dinheiro com inteiros (centavos) e formatar com `Intl.NumberFormat`

## 🤔 Por que isso importa
JavaScript é a **única** linguagem que roda dentro do navegador. Mesmo que seu foco seja o backend em Python, é o JS que faz o catálogo filtrar sem recarregar, o carrinho atualizar e a página chamar a sua API. Em vagas júnior de backend, “saber o suficiente de JS para consumir a API e entender o código do front” é esperado. Além disso, quase todas as armadilhas aqui (comparações, `float`, ordenação) são perguntas clássicas de entrevista.

## 💡 Intuição (explicação simples)
Se Python é uma **língua estrita e organizada** (tipos fortes, poucos jeitos de fazer a mesma coisa), JavaScript é uma **língua falada cheia de dialetos e atalhos**: muito flexível e permissiva (converte tipos sozinha, aceita quase tudo), o que a torna fácil de começar e fácil de errar. A saída é usar o “subconjunto bom”: `const`, `===`, funções pequenas e *arrays* funcionais.

## 🔬 Como funciona por dentro
- **Onde roda:** no navegador (com acesso ao DOM, aula 05) e no **Node.js** (servidor/terminal, sem DOM). Nesta aula usamos o Node 22 para rodar scripts, e `console.log` imprime no terminal; no navegador, o mesmo `console.log` aparece no *Console* do DevTools.
- **Tipagem dinâmica e fraca:** o tipo está no valor, e o JS **converte** valores sozinho (coerção): `"5" * 2` dá `10`, mas `"5" + 2` dá `"52"`. É por isso que se usa `===` (sem coerção).
- **Tipos primitivos:** `number` (sempre *double* IEEE 754, igual ao `float` do Python: sem `int`!), `string`, `boolean`, `null` (ausência intencional), `undefined` (valor ainda não definido), `bigint`, `symbol`. Todo o resto é **objeto** (arrays, funções, datas, `{}`).
- **Escopo:** `const` (não reatribuível) e `let` (reatribuível) têm escopo de **bloco**; `var` tem escopo de **função** e sofre *hoisting* (a declaração “sobe”), fonte de bugs: não use.
- **Funções são valores** (“cidadãs de primeira classe”): podem ser passadas, devolvidas e guardadas. Uma **closure** é uma função que **lembra** as variáveis do escopo onde nasceu, mesmo depois que ele terminou (mesma ideia da aula 1.16).
- **Event loop** (aula 06): o JS roda em **uma thread**; tarefas demoradas (rede, timers) não bloqueiam porque são agendadas.

| Conceito | Python | JavaScript |
|---|---|---|
| Variável | `x = 1` | `const x = 1` / `let x = 1` |
| Números | `int`, `float`, `Decimal` | só `number` (double); `bigint` à parte |
| Texto | `f"{a}"` | `` `${a}` `` (template literal) |
| Vazio | `None` | `null` e `undefined` |
| Igualdade | `==` (valor), `is` (identidade) | `===` (valor+tipo; **use este**), `==` (com coerção) |
| Falsy | `0, "", [], {}, None` | `0, "", null, undefined, NaN, false` (**`[]` e `{}` são truthy**) |
| Lista / dict | `list` / `dict` | `Array` / `Object` (ou `Map`) |
| Laço sobre lista | `for x in xs` | `for (const x of xs)` · `xs.forEach(...)` |
| Compreensão | `[f(x) for x in xs if c]` | `xs.filter(c).map(f)` |
| Exceção | `try/except` | `try/catch` |
| Função anônima | `lambda x: x*2` | `x => x * 2` |

## 🛠️ Exemplo prático
Cada bloco foi executado com o Node 22. (Para rodar: salve em `arquivo.mjs` e `node arquivo.mjs`.)

**1. Variáveis e escopo**
```js
const preco = 49.9;              // não pode ser reatribuída
let estoque = 3;                 // pode
estoque -= 1;

if (true) {
  let dentro = "só no bloco";
  var vaza = "var vaza para a função!";
}
console.log(estoque, typeof vaza);
try { console.log(dentro); } catch (e) { console.log(e.name + ":", e.message); }
try { preco = 10; } catch (e) { console.log(e.name + ":", e.message); }
console.log(typeof naoExiste);               // typeof nunca dá erro
try { naoExiste; } catch (e) { console.log(e.name + ":", e.message); }
console.log(antes);                          // var sofre hoisting: existe, mas é undefined
var antes = 1;
```
```text
2 string
ReferenceError: dentro is not defined
TypeError: Assignment to constant variable.
undefined
ReferenceError: naoExiste is not defined
undefined
```
**2. Tipos e pegadinhas**
```js
console.log(typeof 42, typeof 4.2, typeof "a", typeof true, typeof undefined, typeof null, typeof [], typeof {}, typeof (() => 1));
console.log(Array.isArray([]), Number.isInteger(5.0), 0.1 + 0.2, 0.1 + 0.2 === 0.3, Number.MAX_SAFE_INTEGER, 2 ** 53 === 2 ** 53 + 1);
console.log(NaN === NaN, Number.isNaN("abc" * 2), parseInt("42px"), Number("42px"), Number(""), Number(null), Number(undefined));
console.log(10n ** 20n, typeof 10n);
console.log("5" + 2, "5" - 2, "5" * "2", [] + [], [] + {}, true + 1);
```
```text
number number string boolean undefined object object object function
true true 0.30000000000000004 false 9007199254740991 true
false true 42 NaN 0 0 NaN
100000000000000000000n bigint
52 3 10  [object Object] 2
```
Em JavaScript **só existe `number` (double)**: `0.1 + 0.2` dá o mesmo erro do `float` do Python (aula 1.01). Para dinheiro, guarde **centavos inteiros** (veja a seção 7).

**3. Igualdade e *truthy*/*falsy***
```js
console.log(0 == "", 0 == "0", "" == "0", null == undefined, null == 0, [] == false, "1" == 1);   // coerções malucas de ==
console.log(0 === "", "1" === 1, null === undefined, NaN === NaN);                                  // === não converte
const valores = [0, "", "0", [], {}, null, undefined, NaN, "false", -1];
for (const v of valores) console.log(JSON.stringify(v) ?? String(v), "→", v ? "truthy" : "falsy");
```
```text
true true false true false true true
false false false false
0 → falsy
"" → falsy
"0" → truthy
[] → truthy
{} → truthy
null → falsy
undefined → falsy
null → falsy
"false" → truthy
-1 → truthy
```
Regra: **sempre `===` e `!==`**. Cuidado ao portar do Python: `if (lista)` é **sempre verdadeiro** para array, mesmo vazio; use `lista.length > 0`.

**4. `??` e `?.`: ausência de valor sem erro**
```js
const config = { tema: "", itens: 0, usuario: { nome: "Ana" } };
console.log(config.itens || 10, config.itens ?? 10);              // || trata 0 como "vazio"; ?? só null/undefined
console.log(config.tema || "claro", config.tema ?? "claro");
console.log(config.usuario?.nome, config.convidado?.nome, config.convidado?.endereco.rua);   // ?. evita o TypeError
try { console.log(config.convidado.nome); } catch (e) { console.log(e.name + ":", e.message); }
```
```text
10 0
claro 
Ana undefined undefined
TypeError: Cannot read properties of undefined (reading 'nome')
```
`??` (coalescência nula) e `?.` (encadeamento opcional) são o equivalente ao `dict.get(chave, padrão)` do Python.

**5. Arrays e a “compreensão” funcional**
```js
const produtos = [
  { sku: "PF-01", nome: "Mouse sem fio", centavos: 8990, estoque: 4, ativo: true },
  { sku: "AU-01", nome: "Fone Bluetooth", centavos: 24990, estoque: 0, ativo: true },
  { sku: "MN-04", nome: 'Monitor 27" 4K', centavos: 219900, estoque: 5, ativo: true },
  { sku: "CB-04", nome: "Cabo USB-C 1m", centavos: 2490, estoque: 12, ativo: false },
];
const disponiveis = produtos.filter(p => p.ativo && p.estoque > 0);                // [x for x in xs if cond]
const nomes = disponiveis.map(p => p.nome);                                        // [f(x) for x in xs]
const total = disponiveis.reduce((soma, p) => soma + p.centavos * p.estoque, 0);   // sum(...)
console.log(nomes, total);
console.log(produtos.find(p => p.sku === "AU-01")?.nome, produtos.some(p => p.estoque === 0), produtos.every(p => p.centavos > 0), produtos.map(p => p.sku).includes("MN-04"));
console.log([10, 9, 1, 100].sort(), [10, 9, 1, 100].sort((a, b) => a - b));        // sort() padrão compara TEXTO!
const ordenados = [...produtos].sort((a, b) => b.centavos - a.centavos);           // cópia: sort muda o array original
console.log(ordenados.map(p => p.sku), produtos.map(p => p.sku));
console.log(produtos.toSorted((a, b) => a.estoque - b.estoque).map(p => p.sku));   // toSorted: versão que não muda (Node 20+)
```
```text
[ 'Mouse sem fio', 'Monitor 27" 4K' ] 1135460
Fone Bluetooth true true true
[ 1, 10, 100, 9 ] [ 1, 9, 10, 100 ]
[ 'MN-04', 'AU-01', 'PF-01', 'CB-04' ] [ 'PF-01', 'AU-01', 'MN-04', 'CB-04' ]
[ 'AU-01', 'PF-01', 'MN-04', 'CB-04' ]
```
`sort()` sem função ordena como **texto** (`[1, 10, 100, 9]`) e **modifica** o array; passe sempre o comparador numérico. Prefira `toSorted`/`[...xs].sort()` quando não quiser alterar o original.

**6. Objetos, desestruturação, *spread* e JSON**
```js
const p = { sku: "MN-04", nome: "Monitor", centavos: 219900, tags: ["4k", "ips"] };
const { sku, nome, desconto = 0 } = p;                      // desestruturação com valor padrão
const [primeira, ...resto] = p.tags;
const atualizado = { ...p, centavos: 199900, promo: true }; // cópia com alterações (não muda p)
console.log(sku, nome, desconto, primeira, resto, p.centavos, atualizado.centavos);
console.log(Object.keys(p), Object.entries({ a: 1, b: 2 }).map(([k, v]) => `${k}=${v}`).join("&"));

const texto = JSON.stringify({ ...p, quando: new Date("2026-11-07T10:30:00Z"), indefinido: undefined, nada: null });
console.log(texto);                                          // Date vira string ISO; undefined some
console.log(JSON.parse(texto).quando, typeof JSON.parse(texto).quando);   // volta como STRING, não Date
```
```text
MN-04 Monitor 0 4k [ 'ips' ] 219900 199900
[ 'sku', 'nome', 'centavos', 'tags' ] a=1&b=2
{"sku":"MN-04","nome":"Monitor","centavos":219900,"tags":["4k","ips"],"quando":"2026-11-07T10:30:00.000Z","nada":null}
2026-11-07T10:30:00.000Z string
```
**7. Funções, *arrow functions* e closures**
```js
function soma(a, b = 0) { return a + b; }                   // declaração (sofre hoisting)
const dobro = x => x * 2;                                    // arrow function
const formatar = ({ nome, centavos }, moeda = "R$") => `${nome}: ${moeda} ${(centavos / 100).toFixed(2)}`;
const somaTudo = (...nums) => nums.reduce((a, b) => a + b, 0);
console.log(soma(1), soma(1, 2), dobro(21), formatar({ nome: "Mouse", centavos: 8990 }), somaTudo(1, 2, 3, 4));

function criarContador() {                                   // closure: "count" é privado e persiste
  let count = 0;
  return { incrementar: () => ++count, atual: () => count };
}
const c1 = criarContador(), c2 = criarContador();
c1.incrementar(); c1.incrementar(); c2.incrementar();
console.log(c1.atual(), c2.atual());

const comDesconto = pct => preco => Math.round(preco * (100 - pct) / 100);     // função que devolve função
console.log([10000, 5000].map(comDesconto(10)));

const obj = { nome: "obj", normal() { return this?.nome; }, seta: () => typeof this };
console.log(obj.normal(), (0, obj.normal)(), obj.seta());                       // `this` depende de COMO a função é chamada
```
```text
1 3 42 Mouse: R$ 89.90 10
2 1
[ 9000, 4500 ]
obj undefined undefined
```
Um `function` comum tem o seu próprio `this` (depende de quem chama); uma *arrow function* **herda** o `this` de onde foi escrita. Em código de DOM e *callbacks* isso importa: prefira *arrow functions* para *callbacks* e use `this` só em classes.

**8. Dinheiro: centavos inteiros e `Intl`**
```js
console.log(0.1 + 0.2, 19.99 * 3, 1.005 * 100);             // armadilhas do double
const emCentavos = reais => Math.round(reais * 100);        // converta UMA vez, na entrada
const brl = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });
const total = 1999 * 3;
console.log(total, brl.format(total / 100), brl.format(219900 / 100));
console.log(JSON.stringify(brl.format(1234.5)), new Intl.NumberFormat("pt-BR").format(1234567.891));
console.log(new Date("2026-11-07T10:30:00Z").toLocaleString("pt-BR", { timeZone: "America/Recife", dateStyle: "short", timeStyle: "short" }));
// valores da API vêm como string ("49.90"): converta com cuidado, só para EXIBIR
console.log(brl.format(Number("49.90")), Math.round(Number("49.90") * 100));
```
```text
0.30000000000000004 59.97 100.49999999999999
5997 R$ 59,97 R$ 2.199,00
"R$ 1.234,50" 1.234.567,891
07/11/2026, 07:30
R$ 49,90 4990
```
Regras: guarde e some **centavos inteiros** (ou a string decimal da API e deixe o cálculo para o backend); use `Intl.NumberFormat` apenas para **exibir** (`R$ 2.199,00`, com espaço não separável). Nunca confie em `float` para somar preço.

**9. Erros**
```js
function dividir(a, b) {
  if (b === 0) throw new RangeError("divisão por zero");
  return a / b;
}
class EstoqueInsuficiente extends Error {
  constructor(sku, pedido, disponivel) { super(`${sku}: pedido ${pedido}, disponível ${disponivel}`); this.name = "EstoqueInsuficiente"; this.sku = sku; }
}
for (const tentativa of [() => dividir(1, 0), () => { throw new EstoqueInsuficiente("MN-04", 9, 5); }, () => JSON.parse("{ruim"), () => null.nome]) {
  try { tentativa(); }
  catch (e) { console.log(`${e.name}: ${e.message}`, e instanceof EstoqueInsuficiente ? `(sku=${e.sku})` : ""); }
  finally { /* roda sempre */ }
}
console.log(1 / 0, -1 / 0, 0 / 0);                          // número, NÃO exceção (diferente do Python!)
```
```text
RangeError: divisão por zero 
EstoqueInsuficiente: MN-04: pedido 9, disponível 5 (sku=MN-04)
SyntaxError: Expected property name or '}' in JSON at position 1 (line 1 column 2) 
TypeError: Cannot read properties of null (reading 'nome') 
Infinity -Infinity NaN
```
## ⚠️ Erros comuns e boas práticas
| Mensagem / sintoma | Causa | Solução |
|---|---|---|
| `ReferenceError: x is not defined` | Variável inexistente ou fora do escopo | Declare com `const`/`let`; confira o escopo |
| `TypeError: Assignment to constant variable.` | Reatribuiu uma `const` | Use `let` (ou não reatribua) |
| `TypeError: Cannot read properties of undefined (reading 'nome')` | Acessou propriedade de `undefined`/`null` | `?.`, checar antes, entender de onde vem o `undefined` |
| `TypeError: x is not a function` | Chamou algo que não é função (nome trocado, import errado) | `console.log(typeof x)` |
| `NaN` aparece na tela | Conta com `undefined` ou texto não numérico | Converta e valide (`Number.isNaN`) |
| `[10, 9, 1].sort()` “ordena errado” | Comparação padrão é textual | `sort((a, b) => a - b)` |
| `0.1 + 0.2 !== 0.3`; centavos errados | `number` é double | Centavos inteiros; `toFixed` só para exibir |
| `if (lista)` sempre verdadeiro | `[]` é *truthy* | `lista.length > 0` |
| `"5" + 2 === "52"` | Coerção do `+` | Converta explicitamente (`Number()`) e use `===` |
| JSON: `Unexpected token ... in JSON at position` | Texto não é JSON (HTML de erro, aspas simples) | Cheque o `Content-Type` e o status antes de `.json()` |

- Use `const` por padrão, `let` quando precisar reatribuir, **nunca** `var`.
- Use `===`, evite coerções implícitas, e valide dados externos (a API pode devolver `null`).
- Funções pequenas e puras; `map`/`filter`/`reduce` em vez de laços com índice quando fizer sentido.
- Não construa HTML nem consultas juntando strings com dados do usuário (aula 05, XSS).
- **Ponto e vírgula:** o JS os insere automaticamente (ASI), mas há casos traiçoeiros. Escolha um estilo (com `;`) e deixe o formatador (Prettier) cuidar.

## 🧠 Pausa para lógica
**Problema (carrinho e paginação em JS).** Porte para JavaScript duas funções do Módulo 1/3: `totalCarrinho(itens, cupomPct)` (em **centavos**, arredondando só no final) e `pagina(itens, numero, tamanho)` + `totalPaginas(total, tamanho)` (aula 1.03). Escreva asserts que provem os casos de borda (carrinho vazio, página fora do intervalo).

<details><summary>Dica</summary>
<code>reduce</code> para somar <code>centavos * qtd</code>. Desconto: <code>Math.round(total * (100 - pct) / 100)</code>. Paginação: <code>itens.slice((n - 1) * tam, n * tam)</code> e <code>Math.ceil(total / tam)</code>. Valide <code>n &lt; 1</code>.
</details>

<details><summary>Solução comentada</summary>

```js
import assert from "node:assert/strict";

const totalCarrinho = (itens, cupomPct = 0) => {
  const bruto = itens.reduce((soma, { centavos, qtd }) => soma + centavos * qtd, 0);   // tudo inteiro até aqui
  return Math.round(bruto * (100 - cupomPct) / 100);                                    // arredonda UMA vez, no fim
};
const totalPaginas = (total, tamanho) => Math.ceil(total / tamanho);
const pagina = (itens, numero, tamanho) => {
  if (!Number.isInteger(numero) || numero < 1 || tamanho < 1) throw new RangeError("pagina e tamanho devem ser >= 1");
  return itens.slice((numero - 1) * tamanho, numero * tamanho);
};

assert.equal(totalCarrinho([]), 0);
assert.equal(totalCarrinho([{ centavos: 1999, qtd: 3 }, { centavos: 550, qtd: 2 }]), 7097);
assert.equal(totalCarrinho([{ centavos: 1999, qtd: 3 }, { centavos: 550, qtd: 2 }], 10), 6387);     // 7097 * 0,9 = 6387,3
const itens = Array.from({ length: 23 }, (_, i) => i + 1);
assert.deepEqual(pagina(itens, 3, 10), [21, 22, 23]);
assert.deepEqual(pagina(itens, 4, 10), []);                                                          // fora do intervalo: vazio, sem erro
assert.equal(totalPaginas(23, 10), 3);
assert.throws(() => pagina(itens, 0, 10), RangeError);
console.log("todos os asserts passaram");
```
```text
todos os asserts passaram
```
Mesma lógica das aulas 1.03/1.04, em outra linguagem: o que muda é a sintaxe, não o raciocínio. Em JS o “`Decimal`” é substituído por **inteiros em centavos**.
</details>

**Variação mais difícil:** escreva `agruparPor(lista, fn)` (como `groupBy`) usando `reduce` e use-a para somar o estoque por categoria; compare com `Object.groupBy` (Node 21+).

## 🧩 Exercícios
**1. Fixação**
Preveja a saída e confira: `console.log([1,2,3].map(String), [1,2,3].map(parseInt), "b" + "a" + +"a" + "a", typeof NaN, [] == ![])`.

<details><summary>Solução</summary>

```js
console.log([1,2,3].map(String), [1,2,3].map(parseInt), "b" + "a" + +"a" + "a", typeof NaN, [] == ![]);
```
```text
[ '1', '2', '3' ] [ 1, NaN, NaN ] baNaNa number true
```
`[1, 2, 3].map(parseInt)` dá `[1, NaN, NaN]`: `map` passa **(valor, índice)** e o `parseInt` usa o 2º argumento como base numérica. `typeof NaN` é `"number"`. `[] == ![]` é `true` (coerções). Moral: **não confie em coerção**; passe funções explícitas (`x => parseInt(x, 10)`).
</details>

**2. Aplicação no projeto MiniShop**
Crie `frontend/js/utils.mjs` com as funções utilitárias do front e `frontend/js/utils.test.mjs` com testes usando o *test runner* embutido do Node.

Critérios de pronto:
- [ ] `formatarPreco(centavos)` → `"R$ 2.199,00"` (com `Intl`), `paraCentavos("49.90")` → `4990` (sem `float`: trate a string), `slugify(texto)` (portado da aula 1.07, sem acentos)
- [ ] `totalCarrinho`, `pagina` e `totalPaginas` da pausa de lógica
- [ ] ≥ 10 testes com `node:test` e `node:assert/strict`, incluindo entradas inválidas
- [ ] `cd frontend && node --test` passa (o Node 22 acha sozinho os arquivos `*.test.mjs`)
- [ ] Nenhuma função usa `var`, `==`, nem `float` para somar dinheiro
- [ ] Commit `feat(front): add js utilities with tests`

<details><summary>Solução de referência</summary>

```js
const brl = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });

export const formatarPreco = centavos => brl.format(centavos / 100);

export function paraCentavos(texto) {                       // "49.90" -> 4990, sem passar por float
  const m = /^(\d+)(?:[.,](\d{1,2}))?$/.exec(String(texto).trim());
  if (!m) throw new RangeError(`preço inválido: ${texto}`);
  return Number(m[1]) * 100 + Number((m[2] ?? "").padEnd(2, "0"));
}

export const slugify = texto =>
  texto.normalize("NFKD").replace(/[̀-ͯ]/g, "").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");

export const totalCarrinho = (itens, cupomPct = 0) =>
  Math.round(itens.reduce((s, { centavos, qtd }) => s + centavos * qtd, 0) * (100 - cupomPct) / 100);

export const totalPaginas = (total, tamanho) => Math.ceil(total / tamanho);

export function pagina(itens, numero, tamanho) {
  if (!Number.isInteger(numero) || numero < 1 || tamanho < 1) throw new RangeError("pagina e tamanho devem ser >= 1");
  return itens.slice((numero - 1) * tamanho, numero * tamanho);
}
```
```js
import test from "node:test";
import assert from "node:assert/strict";
import { formatarPreco, paraCentavos, slugify, totalCarrinho, pagina, totalPaginas } from "./utils.mjs";

test("formatarPreco usa o padrão brasileiro", () => {
  assert.match(formatarPreco(219900), /^R\$\s2\.199,00$/);     // o espaço é "não separável", por isso \s
});
test("paraCentavos evita float", () => {
  assert.equal(paraCentavos("49.90"), 4990);
  assert.equal(paraCentavos("49,9"), 4990);
  assert.equal(paraCentavos("5"), 500);
});
test("paraCentavos rejeita entradas inválidas", () => {
  for (const ruim of ["abc", "", "-1", "1.234", "R$ 5"]) assert.throws(() => paraCentavos(ruim), RangeError, ruim);
});
test("slugify", () => {
  assert.equal(slugify("Teclado Mecânico RGB"), "teclado-mecanico-rgb");
  assert.equal(slugify("  Café & Pão!  "), "cafe-pao");
  assert.equal(slugify("@@@"), "");
});
test("carrinho e paginação", () => {
  assert.equal(totalCarrinho([]), 0);
  assert.equal(totalCarrinho([{ centavos: 1999, qtd: 3 }], 10), 5397);
  const xs = Array.from({ length: 23 }, (_, i) => i);
  assert.equal(totalPaginas(23, 10), 3);
  assert.deepEqual(pagina(xs, 3, 10), [20, 21, 22]);
  assert.deepEqual(pagina(xs, 9, 10), []);
  assert.throws(() => pagina(xs, 0, 10), RangeError);
});
```
```bash
cd frontend && node --test 2>&1 | grep -E "^# (tests|pass|fail)|✖|not ok" | head
```
```text
# tests 5
# pass 5
# fail 0
```
(Três casas decimais, como `"1.234"`, não representam centavos: o teste de entradas inválidas garante que `paraCentavos` as rejeita em vez de arredondar em silêncio. Leia sempre o que a asserção realmente prova.)
</details>

**3. Desafio (opcional)**
Implemente `memoize(fn)` e `debounce(fn, ms)` (a aula 05 usa o segundo) e teste com `node:test` e *fake timers* (`mock.timers`).

## 🎤 Na entrevista
- **Qual a diferença entre `==` e `===`?** `==` compara com coerção de tipos (`0 == "0"` é `true`), `===` compara valor **e** tipo; usa-se sempre `===`.
- **Diferença entre `var`, `let` e `const`?** `var`: escopo de função e *hoisting*; `let`: escopo de bloco, reatribuível; `const`: escopo de bloco, sem reatribuição (o objeto referenciado ainda pode mudar).
- **O que é uma closure?** Função que mantém acesso às variáveis do escopo onde foi criada, mesmo depois que ele terminou; permite estado privado e fábricas de funções.
- **Por que `0.1 + 0.2 !== 0.3` e como tratar dinheiro?** O `number` é um double binário (IEEE 754); guardam-se valores monetários em centavos inteiros (ou usa-se uma biblioteca decimal) e formata-se só na exibição.
- **`null` × `undefined`?** `undefined` é “não atribuído/inexistente”; `null` é “vazio” intencional.

## 📚 Para ir além
- 📄 Documentação oficial: [Guia de JavaScript (MDN)](https://developer.mozilla.org/pt-BR/docs/Web/JavaScript/Guide). Tutorial completo, em PT-BR, da linguagem.
- 📄 Documentação oficial: [Scripting: JavaScript (MDN)](https://developer.mozilla.org/pt-BR/docs/Learn_web_development/Core/Scripting). Curso de iniciante.
- 📑 Artigo/tutorial: [The Modern JavaScript Tutorial](https://javascript.info/). Gratuito e excelente (EN; há tradução PT-BR).
- 📄 Documentação oficial: [Node.js: test runner](https://nodejs.org/api/test.html). `node:test` e `node:assert`.
- 🏋️ Prática extra: resolva em JS os 5 exercícios de lógica da aula 1.03 (laços) e da 1.06 (dicionários).

## ✅ Checklist da aula
- [ ] Rodei os 9 exemplos no Node e conferi as saídas
- [ ] Provoquei `ReferenceError`, `TypeError` e `NaN` de propósito
- [ ] Reescrevi `totalCarrinho` e `pagina` em JS, com asserts
- [ ] Usei `===`, `const` e centavos inteiros
- [ ] Fiz o commit do exercício
