# Cheatsheet: HTML · CSS · JavaScript (Módulo 4)

```html
<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>…</title></head>
<body><header><nav aria-label="Principal"></nav></header><main><h1></h1></main><footer></footer></body></html>
<label for="x">Rótulo</label><input id="x" name="x" type="email" required autocomplete="email">   <!-- name = chave enviada -->
```
```css
*, *::before, *::after { box-sizing: border-box; }
:root { --cor: #0b5fff; }  .card { padding: 1rem; color: var(--cor); }
.linha { display: flex; gap: 1rem; justify-content: space-between; align-items: center; flex-wrap: wrap; }
.grade { display: grid; grid-template-columns: repeat(auto-fill, minmax(14rem, 1fr)); gap: 1rem; }
@media (min-width: 48rem) { … }          :focus-visible { outline: 3px solid #b35900; }
```
Especificidade: (ids, classes/atributos/pseudo-classes, tags); `!important` > inline > id > classe > tag.
```js
const $ = s => document.querySelector(s);    el.textContent = dado;   // NUNCA innerHTML com dado externo
lista.addEventListener("click", e => { const b = e.target.closest("button[data-sku]"); if (b) … });   // delegação
const r = await fetch(url, { method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(obj) });
if (!r.ok) throw new Error(r.status);  const dados = await r.json();       // fetch NÃO rejeita em 4xx/5xx
await Promise.all([a(), b()]);  AbortSignal.timeout(4000);  new Intl.NumberFormat("pt-BR", {style:"currency", currency:"BRL"});
```
Armadilhas: `===`, `[]` é truthy, `sort((a,b)=>a-b)`, centavos inteiros, `new Date(a, m-1, d)` para datas de calendário, CORS é do navegador.
Acessibilidade: semântica → rótulos/`alt` → teclado e foco visível → contraste ≥ 4,5:1 → ARIA só se preciso → axe + teclado + leitor de tela.
