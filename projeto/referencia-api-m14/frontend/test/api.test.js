import assert from "node:assert/strict";
import { beforeEach, test } from "node:test";

// sessionStorage de mentira (o Node não tem)
class Armazem { #d = new Map(); getItem(k) { return this.#d.get(k) ?? null; } setItem(k, v) { this.#d.set(k, String(v)); } removeItem(k) { this.#d.delete(k); } }
globalThis.sessionStorage = new Armazem();
globalThis.MINISHOP_API = "http://api.teste/api/v1";

const { requisitar, ApiError, entrar, api } = await import("../js/api.js");
const { guardarTokens, lerTokens, limparTokens } = await import("../js/session.js");

const json = (status, corpo, extra = {}) =>
  new Response(corpo === null ? null : JSON.stringify(corpo), { status, headers: { "Content-Type": "application/json", ...extra } });

let chamadas;
function simular(...respostas) {
  chamadas = [];
  globalThis.fetch = async (url, opcoes) => {
    chamadas.push({ url, ...opcoes });
    const r = respostas.shift();
    if (r instanceof Error) throw r;
    return typeof r === "function" ? r() : r;
  };
}

beforeEach(() => { limparTokens(); });

test("envia o Bearer quando há token e JSON no corpo", async () => {
  guardarTokens({ access: "AAA", refresh: "RRR" });
  simular(json(200, { ok: true }));
  await requisitar("/cart/items/", { metodo: "POST", corpo: { product: 2 } });
  assert.equal(chamadas[0].headers.Authorization, "Bearer AAA");
  assert.equal(chamadas[0].headers["Content-Type"], "application/json");
  assert.equal(chamadas[0].body, '{"product":2}');
});

test("não envia Authorization em chamadas públicas", async () => {
  guardarTokens({ access: "AAA", refresh: "RRR" });
  simular(json(200, { results: [] }));
  await api.produtos({ search: "mouse" });
  assert.equal(chamadas[0].headers.Authorization, undefined);
  assert.match(chamadas[0].url, /\/products\/\?search=mouse$/);
});

test("204 devolve null", async () => {
  simular(new Response(null, { status: 204 }));
  assert.equal(await requisitar("/cart/items/1/", { metodo: "DELETE", autenticado: false }), null);
});

test("erro de validação (400) vira ApiError com fields", async () => {
  simular(json(400, { quantity: ["Deve ser >= 1."] }));
  await assert.rejects(requisitar("/cart/items/", { metodo: "POST", corpo: {} }), (e) =>
    e instanceof ApiError && e.status === 400 && e.code === "validation_error" && e.fields.quantity[0] === "Deve ser >= 1.");
});

test("erro de regra (422) vira ApiError com detail e code", async () => {
  simular(json(422, { detail: "Seu carrinho está vazio.", code: "empty_cart" }));
  await assert.rejects(requisitar("/orders/", { metodo: "POST" }), (e) => e.status === 422 && e.code === "empty_cart" && e.detail === "Seu carrinho está vazio.");
});

test("429 guarda o Retry-After", async () => {
  simular(json(429, { detail: "Pedido foi suprimido.", code: "throttled" }, { "Retry-After": "60" }));
  await assert.rejects(entrar("a", "b"), (e) => e.status === 429 && e.retryAfter === "60");
});

test("falha de rede vira network_error (status 0)", async () => {
  simular(new TypeError("Failed to fetch"));
  await assert.rejects(requisitar("/products/", { autenticado: false }), (e) => e.status === 0 && e.code === "network_error");
});

test("401 token_not_valid → renova UMA vez e repete a chamada com o novo token", async () => {
  guardarTokens({ access: "VELHO", refresh: "R1" });
  simular(
    json(401, { detail: "expirado", code: "token_not_valid" }),
    json(200, { access: "NOVO", refresh: "R2" }),
    json(200, { items: [], total: "0.00", count: 0 }),
  );
  const carrinho = await api.carrinho();
  assert.equal(carrinho.count, 0);
  assert.equal(chamadas.length, 3);
  assert.match(chamadas[1].url, /\/auth\/token\/refresh\/$/);
  assert.equal(chamadas[2].headers.Authorization, "Bearer NOVO");
  assert.deepEqual(lerTokens(), { access: "NOVO", refresh: "R2" });          // refresh rotacionado foi guardado
});

test("várias chamadas com 401 ao mesmo tempo compartilham um único refresh (single-flight)", async () => {
  guardarTokens({ access: "VELHO", refresh: "R1" });
  let refreshes = 0;
  globalThis.fetch = async (url, opcoes) => {
    if (url.endsWith("/auth/token/refresh/")) { refreshes++; await new Promise((r) => setTimeout(r, 20)); return json(200, { access: "NOVO", refresh: "R2" }); }
    return opcoes.headers.Authorization === "Bearer NOVO" ? json(200, { ok: 1 }) : json(401, { detail: "x", code: "token_not_valid" });
  };
  const resultados = await Promise.all([api.carrinho(), api.pedidos(), api.carrinho()]);
  assert.equal(resultados.length, 3);
  assert.equal(refreshes, 1);
});

test("se o refresh falha: limpa a sessão e lança session_expired", async () => {
  guardarTokens({ access: "VELHO", refresh: "R1" });
  simular(json(401, { detail: "x", code: "token_not_valid" }), json(401, { detail: "blacklist", code: "token_not_valid" }));
  await assert.rejects(api.carrinho(), (e) => e.code === "session_expired" && e.status === 401);
  assert.equal(lerTokens(), null);
});

test("401 em chamada pública NÃO tenta refresh", async () => {
  guardarTokens({ access: "A", refresh: "R" });
  simular(json(401, { detail: "x", code: "token_not_valid" }));
  await assert.rejects(requisitar("/products/", { autenticado: false }), (e) => e.status === 401);
  assert.equal(chamadas.length, 1);
});

test("finalizarPedido envia o cabeçalho Idempotency-Key", async () => {
  guardarTokens({ access: "A", refresh: "R" });
  simular(json(201, { id: 7 }));
  await api.finalizarPedido("chave-123");
  assert.equal(chamadas[0].headers["Idempotency-Key"], "chave-123");
  assert.equal(chamadas[0].method, "POST");
});
