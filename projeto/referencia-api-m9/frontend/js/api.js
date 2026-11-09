import { guardarTokens, lerTokens, limparTokens } from "./session.js";

export const BASE = globalThis.MINISHOP_API ?? "http://127.0.0.1:8131/api/v1";
const TIMEOUT_MS = 10_000;

export class ApiError extends Error {
  constructor({ status, code = "error", detail = "Erro inesperado.", fields = null, retryAfter = null }) {
    super(detail);
    Object.assign(this, { name: "ApiError", status, code, detail, fields, retryAfter });
  }
}

// Formato de erro da API (aula 6.05): {"campo": [...]} para validação; {"detail", "code"} para o resto.
async function lerErro(resposta) {
  let corpo = null;
  try { corpo = await resposta.json(); } catch { /* corpo vazio ou não-JSON */ }
  const retryAfter = resposta.headers.get("Retry-After");
  if (corpo && typeof corpo.detail === "string") {
    return new ApiError({ status: resposta.status, code: corpo.code, detail: corpo.detail, retryAfter });
  }
  if (corpo && typeof corpo === "object") {
    return new ApiError({ status: resposta.status, code: "validation_error", detail: "Corrija os campos destacados.", fields: corpo });
  }
  return new ApiError({ status: resposta.status, detail: `Falha (HTTP ${resposta.status}).` });
}

async function enviar(url, { metodo = "GET", corpo, token, cabecalhos = {} } = {}) {
  const ctl = new AbortController();
  const timer = setTimeout(() => ctl.abort(), TIMEOUT_MS);
  try {
    const resposta = await fetch(url, {
      method: metodo,
      signal: ctl.signal,
      headers: {
        Accept: "application/json",
        ...(corpo !== undefined && { "Content-Type": "application/json" }),
        ...(token && { Authorization: `Bearer ${token}` }),
        ...cabecalhos,
      },
      body: corpo === undefined ? undefined : JSON.stringify(corpo),
    });
    if (!resposta.ok) throw await lerErro(resposta);
    return resposta.status === 204 ? null : await resposta.json();
  } catch (e) {
    if (e instanceof ApiError) throw e;
    if (e.name === "AbortError") throw new ApiError({ status: 0, code: "timeout", detail: "A API demorou demais para responder." });
    throw new ApiError({ status: 0, code: "network_error", detail: "Sem conexão com a API (ou bloqueado por CORS)." });
  } finally {
    clearTimeout(timer);
  }
}

// "Single-flight": várias chamadas que recebem 401 ao mesmo tempo compartilham UM único refresh.
let refreshEmAndamento = null;

function renovar() {
  refreshEmAndamento ??= (async () => {
    const tokens = lerTokens();
    if (!tokens?.refresh) throw new ApiError({ status: 401, code: "not_authenticated", detail: "Faça login novamente." });
    try {
      const novo = await enviar(`${BASE}/auth/token/refresh/`, { metodo: "POST", corpo: { refresh: tokens.refresh } });
      guardarTokens({ access: novo.access, refresh: novo.refresh ?? tokens.refresh });   // a API rotaciona o refresh
    } catch (e) {
      limparTokens();
      throw new ApiError({ status: 401, code: "session_expired", detail: "Sua sessão expirou. Entre novamente." });
    }
  })().finally(() => { refreshEmAndamento = null; });
  return refreshEmAndamento;
}

export async function requisitar(caminhoOuUrl, opcoes = {}) {
  const url = caminhoOuUrl.startsWith("http") ? caminhoOuUrl : `${BASE}${caminhoOuUrl}`;
  const { autenticado = true, ...resto } = opcoes;
  const tentar = () => enviar(url, { ...resto, token: autenticado ? lerTokens()?.access : undefined });
  try {
    return await tentar();
  } catch (e) {
    const tokenInvalido = e instanceof ApiError && e.status === 401 && e.code === "token_not_valid";
    if (!autenticado || !tokenInvalido) throw e;
    await renovar();                 // se falhar, lança session_expired
    return tentar();                 // uma segunda e última tentativa
  }
}

export async function entrar(username, password) {
  const tokens = await requisitar("/auth/token/", { metodo: "POST", corpo: { username, password }, autenticado: false });
  guardarTokens(tokens);
}

export const sair = async () => {
  const tokens = lerTokens();
  limparTokens();
  if (tokens?.refresh) {                                   // invalida o refresh no servidor (melhor esforço)
    try { await enviar(`${BASE}/auth/logout/`, { metodo: "POST", corpo: { refresh: tokens.refresh } }); } catch { /* ok */ }
  }
};

export const api = {
  produtos: (params = {}) => requisitar(`/products/?${new URLSearchParams(params)}`, { autenticado: false }),
  categorias: () => requisitar("/categories/", { autenticado: false }),
  carrinho: () => requisitar("/cart/"),
  adicionar: (product, quantity = 1) => requisitar("/cart/items/", { metodo: "POST", corpo: { product, quantity } }),
  alterarQuantidade: (itemId, quantity) => requisitar(`/cart/items/${itemId}/`, { metodo: "PATCH", corpo: { quantity } }),
  remover: (itemId) => requisitar(`/cart/items/${itemId}/`, { metodo: "DELETE" }),
  finalizarPedido: (chave) => requisitar("/orders/", { metodo: "POST", cabecalhos: { "Idempotency-Key": chave } }),
  pedidos: () => requisitar("/orders/"),
};
