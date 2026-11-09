import puppeteer from "puppeteer-core";

const passos = [];
const ok = (nome, cond, detalhe = "") => { passos.push([cond ? "OK " : "FALHOU", nome, detalhe]); if (!cond) process.exitCode = 1; };

const browser = await puppeteer.launch({ executablePath: "/usr/bin/google-chrome", headless: "new", args: ["--no-sandbox", "--disable-gpu"] });
const page = await browser.newPage();
await page.setViewport({ width: 1200, height: 800 });
const errosDeConsole = [];
page.on("pageerror", (e) => errosDeConsole.push(e.message));
page.on("console", (m) => { if (m.type() === "error" && !/status of 401/.test(m.text())) errosDeConsole.push(m.text()); });   // o 401 é o da senha errada, provocado de propósito

const texto = (sel) => page.$eval(sel, (e) => e.textContent.trim());
const esperarTexto = (sel, regex) => page.waitForFunction((s, r) => new RegExp(r).test(document.querySelector(s)?.textContent ?? ""), { timeout: 8000 }, sel, regex);

await page.goto("http://127.0.0.1:8200/index.html");
await page.waitForSelector("#produtos .card");
ok("catálogo carrega com 20 cards (1ª página)", (await page.$$("#produtos .card")).length === 20, await texto("#resumo"));
ok("categorias carregadas no filtro", (await page.$$("#categoria option")).length === 4);

await page.type("#busca", "mouse");
await page.click("#filtros button[type=submit]");
await esperarTexto("#resumo", "^4 produto");
ok("busca 'mouse' → 4 produtos", (await page.$$("#produtos .card")).length === 4);

await page.$eval("#busca", (e) => (e.value = ""));
await page.click("#filtros button[type=submit]");
await esperarTexto("#resumo", "^6[0-9] produto");
await page.click("#proxima");
await page.waitForFunction(() => document.querySelector("#anterior").disabled === false, { timeout: 8000 });
ok("paginação: botão 'Anterior' habilitado na página 2", true);
await page.click("#anterior");
await page.waitForFunction(() => document.querySelector("#anterior").disabled === true, { timeout: 8000 });

await page.$eval("#busca", (e) => (e.value = "XSS-001"));
await page.click("#filtros button[type=submit]");
await esperarTexto("#resumo", "^1 produto");
const imgs = await page.$$("#produtos img");
ok("XSS: produto com <img onerror> aparece como TEXTO (nenhuma <img> criada)", imgs.length === 0, "título da página: " + (await page.title()));
ok("XSS: o código malicioso não executou (título continua 'MiniShop')", (await page.title()) === "MiniShop");
ok("XSS: o texto do nome é exibido literalmente", (await texto("#produtos .card h3")).startsWith("<img src=x"));

await page.$eval("#busca", (e) => (e.value = "Mouse"));
await page.click("#filtros button[type=submit]");
await esperarTexto("#resumo", "^4 produto");
await page.click("#produtos .card button");
await page.waitForSelector("#dlg-login[open]");
ok("adicionar sem login abre o diálogo de login", true);

await page.type("#form-login [name=username]", "cliente");
await page.type("#form-login [name=password]", "senha-errada");
await page.click("#form-login button[type=submit]");
await esperarTexto("#erro-login", "incorreto");
ok("senha errada mostra o erro da API no diálogo", true, await texto("#erro-login"));

await page.$eval("#form-login [name=password]", (e) => (e.value = ""));
await page.type("#form-login [name=password]", "dev-somente-local-123");
await page.click("#form-login button[type=submit]");
await page.waitForFunction(() => !document.querySelector("#dlg-login").open, { timeout: 8000 });
ok("login correto fecha o diálogo e mostra 'Sair'", (await page.$eval("#btn-sair", (e) => !e.hidden)) === true);

await page.click("#produtos .card button");
await esperarTexto("#contador", "^1$");
ok("adicionar ao carrinho atualiza o contador (1) e o total", /R\$/.test(await texto("#total")), await texto("#total"));

await page.click("#finalizar");
await esperarTexto("#avisos", "Pedido #");
ok("finalizar cria o pedido e mostra a confirmação", true, await texto("#avisos"));
await esperarTexto("#contador", "^0$");
ok("carrinho esvaziado depois do pedido", (await texto("#contador")) === "0");

await page.screenshot({ path: process.argv[2] ?? "minishop.png" });
await page.reload();
await page.waitForSelector("#produtos .card");
ok("recarregar a página mantém a sessão (sessionStorage)", (await page.$eval("#btn-sair", (e) => !e.hidden)) === true);

ok("nenhum erro no console do navegador", errosDeConsole.length === 0, errosDeConsole.join(" | "));
await browser.close();
for (const [s, n, d] of passos) console.log(`${s} ${n}${d ? "  → " + d : ""}`);
