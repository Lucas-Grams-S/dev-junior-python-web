// Tokens em sessionStorage: somem ao fechar a aba. É um meio-termo (veja "Onde guardar os tokens?" na aula).
const CHAVE = "minishop.tokens";

function armazem() {
  try { return globalThis.sessionStorage ?? null; } catch { return null; }   // pode lançar em modo privado
}

export function lerTokens() {
  try { return JSON.parse(armazem()?.getItem(CHAVE) ?? "null"); } catch { return null; }
}

export function guardarTokens(tokens) {
  try { armazem()?.setItem(CHAVE, JSON.stringify(tokens)); } catch { /* sem armazenamento: vale só em memória */ }
}

export function limparTokens() {
  try { armazem()?.removeItem(CHAVE); } catch { /* ignora */ }
}

export const estaLogado = () => Boolean(lerTokens()?.access);
