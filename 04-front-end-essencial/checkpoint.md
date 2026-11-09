# Checkpoint — Módulo 4: Front-end essencial para dev backend

> ⏱️ ~1h30 · Faça **sem consultar** as aulas na primeira tentativa. 30 min para o quiz, 60 min para a entrega.

## 📝 Quiz (10 questões)
1. O que torna um HTML “semântico”? Escreva a estrutura mínima de uma página e diga o que cada `meta` essencial faz.
2. Como um `<form>` vira uma requisição HTTP? Qual a diferença entre `GET` e `POST`, e por que um campo sem `name` ou um *checkbox* desmarcado não chega ao servidor? Basta validar no navegador?
3. Explique a cascata do CSS e calcule a especificidade de `#menu .item a:hover` e `div.b.c`. Quem vence entre `.a .b` e `div.b.c`?
4. Descreva o *box model*. Com `width: 300px; padding: 20px; border: 5px solid`, qual a largura final em `content-box` e em `border-box`? Por que as margens verticais “colapsam”?
5. Quando usar Flexbox e quando Grid? O que faz `grid-template-columns: repeat(auto-fill, minmax(14rem, 1fr))`? O que é *mobile-first*?
6. Cite 4 diferenças/pegadinhas do JavaScript em relação ao Python (tipos, igualdade, *truthy*/*falsy*, `sort`, números) e como tratar dinheiro.
7. O que é uma closure? Qual a diferença entre `var`, `let` e `const`? E entre `null` e `undefined`?
8. Explique o *event loop*: em que ordem executam código síncrono, `Promise.then` e `setTimeout(…, 0)`? O que `fetch` faz com um `404` e com um servidor fora do ar?
9. O que é XSS e como evitá-lo no DOM? O que é *event bubbling* e delegação de eventos? Para que serve o *debounce*?
10. O que é CORS e quem o impõe? Por que o `POST` com JSON gera um `OPTIONS`? Cite 4 práticas de acessibilidade e a razão mínima de contraste em AA.

<details><summary>Gabarito</summary>

1. Usar tags pelo significado (`header`, `nav`, `main`, `article`, `button`, `label`…) em vez de `div` para tudo: melhora acessibilidade, SEO e manutenção. Mínimo: `<!doctype html>`, `<html lang="pt-BR">`, `<head>` com `<meta charset="utf-8">` (acentos), `<meta name="viewport" content="width=device-width, initial-scale=1">` (layout móvel) e `<title>`; `<body>` com `header`/`main`/`footer`.
2. O navegador reúne os campos com `name` e envia: `GET` como query string (consultas, idempotente, URL compartilhável), `POST` no corpo (`x-www-form-urlencoded` ou `multipart`) para criar/alterar. Campos sem `name`, desabilitados ou *checkboxes* desmarcados não são enviados. **Não**: a validação do navegador é conforto e pode ser burlada; o servidor sempre revalida.
3. Importância (`!important`) → especificidade → ordem. `#menu .item a:hover` = (1,2,1); `div.b.c` = (0,2,1). `.a .b` = (0,2,0) perde para `div.b.c` (0,2,1). A comparação é por faixas (11 classes não vencem 1 id).
4. Conteúdo + *padding* + borda + margem (por fora). `content-box`: 350 px; `border-box`: 300 px. Margens verticais adjacentes de blocos colapsam (vale a maior); não colapsam em flex/grid nem com `flow-root`.
5. Flexbox: uma dimensão (barras, centralização, componentes); Grid: duas dimensões (páginas, catálogos). O `repeat(auto-fill, minmax(14rem, 1fr))` cria quantas colunas de pelo menos 14 rem couberem e reparte a sobra. *Mobile-first*: CSS base para tela pequena e ampliação com `@media (min-width: …)`.
6. Só existe `number` (double; `0.1 + 0.2 !== 0.3`); `==` converte tipos, use `===`; `[]` e `{}` são *truthy* (use `.length`); `sort()` ordena como texto e muda o array; `NaN !== NaN`; `1/0` não é exceção. Dinheiro: centavos inteiros (ou string da API) e `Intl.NumberFormat` só para exibir.
7. Closure: função que mantém acesso às variáveis do escopo onde nasceu. `var`: escopo de função + *hoisting*; `let`: bloco, reatribuível; `const`: bloco, sem reatribuição. `undefined`: não definido; `null`: vazio intencional.
8. Primeiro todo o código síncrono, depois as **microtarefas** (Promises/`await`), depois as **tarefas** (`setTimeout`, eventos). `fetch` **resolve** com `ok === false` para 404/500 (é preciso conferir `response.ok`) e **rejeita** (`TypeError`) em erro de rede.
9. XSS: script injetado por dado não escapado; evita-se com `textContent`/`createElement` (nunca `innerHTML` com dado externo) e sanitização/CSP. *Bubbling*: o evento sobe do alvo pelos ancestrais; delegação = um único *listener* no ancestral usando `event.target.closest(...)`. *Debounce*: executa só depois que o usuário para de disparar o evento por um intervalo.
10. CORS: o servidor declara por cabeçalhos quais origens podem **ler** suas respostas; é **imposto pelo navegador** (o servidor recebe a requisição). JSON (`Content-Type: application/json`), `Authorization` e métodos como `PUT`/`DELETE` exigem *preflight* `OPTIONS`. Acessibilidade: HTML semântico, `label`, `alt`, foco visível/teclado, ARIA só se preciso, contraste ≥ **4,5:1** (3:1 para texto grande e componentes).
</details>

## 🛠️ Entrega prática
Repositório `minishop` na tag `v0.4-front-estatico`, com `frontend/`:
- [ ] Páginas semânticas e válidas: `index.html` (catálogo), `produto.html`, `checkout.html`, `feriados.html` (ou outra API pública), todas com `lang`, `viewport`, `title`, marcos e títulos em ordem
- [ ] `style.css` único com variáveis, `border-box`, Flexbox no cabeçalho e Grid no catálogo, responsivo (375, 768, 1280 px) sem rolagem horizontal e sem `!important`
- [ ] JavaScript em módulos ES: `utils.mjs`, `api.mjs` (erros tipados, *timeout*, *retry*), `debounce.mjs`, `busca.mjs`, `cep.mjs`, `feriados.mjs`, `catalogo.mjs`; **nenhum** `innerHTML` com dado externo
- [ ] Catálogo ligado à **sua** API (`minishop_http` com `CORS_ORIGIN`), com busca, ordenação, paginação e os quatro estados (carregando/sucesso/vazio/erro)
- [ ] Testes: `cd frontend && node --test` verde (utils, api, cep, ≥ 15 blocos de teste no total) **e** páginas de teste de ponta a ponta no Chrome com a saída registrada
- [ ] Auditoria de acessibilidade: 0 violações do axe nas páginas, teste só com teclado e razões de contraste (`docs/acessibilidade.md`)
- [ ] `docs/cors.md`, `docs/decisoes.md` (React/Vue × Django+HTMX) e capturas (desktop e mobile) em `docs/img/`
- [ ] Tag publicada: `git tag v0.4-front-estatico && git push --tags`

**Prova de fogo (40 min, sem consultar):** (1) escreva uma função `debounce` e um teste com *fake timers* (`node:test` + `mock.timers`); (2) faça `fetch` de uma URL e trate `404`, `500` e servidor fora do ar de formas diferentes; (3) deixe um `<div onclick>` acessível sem usar ARIA (qual elemento você usa?).

## 🪞 Autoavaliação
Nota de 0 a 3. Se algum item ficar em **0 ou 1**, refaça a aula antes de seguir.

| Habilidade | Aula | Nota |
|---|---|---|
| HTML semântico e formulários (GET/POST, `name`) | 01 | |
| Cascata, especificidade, box model, `rem` | 02 | |
| Flexbox, Grid e design responsivo | 03 | |
| Tipos, igualdade, funções, closures, centavos em JS | 04 | |
| DOM, eventos, delegação, XSS, *debounce* | 05 | |
| Event loop, Promises, `fetch`, CORS | 06 | |
| Consumir APIs com os 4 estados, datas, CEP | 07 | |
| React/Vue/HTMX (conversar) e acessibilidade (axe, contraste) | 08 | |

## 🧠 Lógica: lista de verificação
Resolveu sem olhar: calculadora de especificidade (02), número de colunas do `auto-fill` com fórmula verificada (03), carrinho em centavos e paginação em JS (04), índice de busca × busca linear (05), `mapLimit` com pico de concorrência (06), cache de CEP com TTL e deduplicação (07), contraste WCAG e ajuste de cor por busca binária (08)? Marque o que faltou e refaça.

➡️ Próximo: [Módulo 5 — Framework web: Django](../05-django/README.md).
