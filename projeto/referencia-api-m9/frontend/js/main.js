import { api, ApiError, entrar, requisitar, sair } from "./api.js";
import { estaLogado } from "./session.js";
import { aviso, el, mensagemDeErro, moeda } from "./ui.js";

const $ = (id) => document.getElementById(id);
const estado = { urlAtual: null };

// ---------- catálogo ----------
async function carregarCatalogo(url = null) {
  const lista = $("produtos");
  lista.setAttribute("aria-busy", "true");
  lista.replaceChildren(el("li", { class: "estado" }, "Carregando…"));
  try {
    const params = { search: $("busca").value.trim(), category: $("categoria").value, ordering: $("ordem").value };
    for (const k of Object.keys(params)) if (!params[k]) delete params[k];
    const dados = url ? await requisitar(url, { autenticado: false }) : await api.produtos(params);
    estado.urlAtual = url;
    desenharProdutos(dados);
  } catch (e) {
    lista.replaceChildren(el("li", { class: "estado erro", role: "alert" }, mensagemDeErro(e), " ",
      el("button", { type: "button", onclick: () => carregarCatalogo(url) }, "Tentar de novo")));
  } finally {
    lista.removeAttribute("aria-busy");
  }
}

function desenharProdutos(dados) {
  const lista = $("produtos");
  if (dados.results.length === 0) {
    lista.replaceChildren(el("li", { class: "estado" }, "Nenhum produto encontrado."));
  } else {
    lista.replaceChildren(...dados.results.map((p) => el("li", { class: "card", "data-sku": p.sku },
      el("h3", {}, p.name),
      el("p", { class: "suave" }, `${p.category.name} · ${p.sku}`),
      el("p", { class: "preco" }, moeda(p.price)),
      p.in_stock
        ? el("button", { type: "button", onclick: () => adicionar(p) }, "Adicionar ao carrinho")
        : el("span", { class: "suave" }, "Sem estoque"))));
  }
  $("resumo").textContent = `${dados.count} produto(s)`;
  $("anterior").disabled = !dados.previous;
  $("proxima").disabled = !dados.next;
  $("anterior").onclick = () => carregarCatalogo(dados.previous);
  $("proxima").onclick = () => carregarCatalogo(dados.next);
}

async function carregarCategorias() {
  try {
    const dados = await api.categorias();
    $("categoria").append(...dados.results.map((c) => el("option", { value: c.slug }, c.name)));
  } catch { /* o filtro simplesmente fica só com "Todas" */ }
}

// ---------- carrinho ----------
async function adicionar(produto) {
  if (!estaLogado()) { $("dlg-login").showModal(); return; }
  try {
    await api.adicionar(produto.id, 1);
    aviso(`“${produto.name}” adicionado ao carrinho.`, "ok");
    await atualizarCarrinho();
  } catch (e) { tratarErro(e); }
}

async function atualizarCarrinho() {
  if (!estaLogado()) { $("itens").replaceChildren(el("li", { class: "suave" }, "Entre para ver seu carrinho.")); $("contador").textContent = "0"; $("total").textContent = ""; $("finalizar").disabled = true; return; }
  try {
    const c = await api.carrinho();
    $("contador").textContent = String(c.count);
    $("total").textContent = `Total: ${moeda(c.total)}`;
    $("finalizar").disabled = c.items.length === 0;
    $("itens").replaceChildren(...(c.items.length ? c.items.map((i) => el("li", { "data-item": i.id },
      el("span", {}, `${i.product.name} × `),
      el("input", { type: "number", min: "0", max: String(i.product.stock), value: String(i.quantity), "aria-label": `Quantidade de ${i.product.name}`,
        onchange: (ev) => alterar(i.id, Number(ev.target.value)) }),
      el("span", {}, ` ${moeda(i.subtotal)} `),
      el("button", { type: "button", "aria-label": `Remover ${i.product.name}`, onclick: () => alterar(i.id, 0) }, "Remover")))
      : [el("li", { class: "suave" }, "Carrinho vazio.")]));
  } catch (e) { tratarErro(e); }
}

async function alterar(itemId, quantidade) {
  try { await api.alterarQuantidade(itemId, quantidade); } catch (e) { tratarErro(e); }
  await atualizarCarrinho();
}

// ---------- pedido ----------
let chaveDaCompra = null;     // UMA chave por intenção de compra: se o usuário clicar duas vezes ou a rede falhar, reaproveita

async function finalizar() {
  $("finalizar").disabled = true;
  chaveDaCompra ??= crypto.randomUUID();
  try {
    const pedido = await api.finalizarPedido(chaveDaCompra);
    chaveDaCompra = null;               // compra concluída: a próxima intenção usa outra chave
    aviso(`Pedido #${pedido.id} criado! Total ${moeda(pedido.total)}.`, "ok");
    await Promise.all([atualizarCarrinho(), carregarCatalogo(estado.urlAtual)]);
  } catch (e) {
    if (e.status !== 0 && e.status !== 429) chaveDaCompra = null;     // falha "definitiva": nova tentativa = nova intenção
    tratarErro(e);
    $("finalizar").disabled = false;
  }
}

// ---------- login ----------
async function enviarLogin(ev) {
  ev.preventDefault();
  const form = ev.target;
  $("erro-login").textContent = "";
  try {
    await entrar(form.username.value, form.password.value);
    form.reset();
    $("dlg-login").close();
    aviso("Login realizado.", "ok");
    await Promise.all([atualizarSessao(), atualizarCarrinho()]);
  } catch (e) {
    $("erro-login").textContent = mensagemDeErro(e);
  }
}

async function atualizarSessao() {
  $("btn-entrar").hidden = estaLogado();
  $("btn-sair").hidden = !estaLogado();
}

function tratarErro(e) {
  if (e instanceof ApiError && e.code === "session_expired") { atualizarSessao(); atualizarCarrinho(); $("dlg-login").showModal(); }
  aviso(mensagemDeErro(e), "erro");
}

// ---------- inicialização ----------
function iniciar() {
  $("filtros").addEventListener("submit", (ev) => { ev.preventDefault(); carregarCatalogo(); });
  $("btn-entrar").addEventListener("click", () => $("dlg-login").showModal());
  $("btn-sair").addEventListener("click", async () => { await sair(); await Promise.all([atualizarSessao(), atualizarCarrinho()]); aviso("Você saiu.", "info"); });
  $("form-login").addEventListener("submit", enviarLogin);
  $("cancelar-login").addEventListener("click", () => $("dlg-login").close());
  $("finalizar").addEventListener("click", finalizar);
  atualizarSessao();
  carregarCategorias();
  carregarCatalogo();
  atualizarCarrinho();
}

iniciar();
