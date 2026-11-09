// Funções puras de apresentação. REGRA: dado vindo da API entra SEMPRE por textContent/createElement, nunca por innerHTML.
export const moeda = (decimalComoTexto) =>
  new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(Number(decimalComoTexto));   // só para EXIBIR

export function el(tag, atributos = {}, ...filhos) {
  const no = document.createElement(tag);
  for (const [k, v] of Object.entries(atributos)) {
    if (k === "class") no.className = v;
    else if (k.startsWith("on")) no.addEventListener(k.slice(2), v);
    else no.setAttribute(k, v);
  }
  no.append(...filhos);                      // strings viram nós de TEXTO (sem interpretar HTML)
  return no;
}

export function aviso(mensagem, tipo = "info") {
  const area = document.getElementById("avisos");
  const p = el("p", { class: `aviso ${tipo}` }, mensagem);
  area.replaceChildren(p);
  return p;
}

export function mensagemDeErro(e) {
  if (e.fields) return Object.entries(e.fields).map(([campo, msgs]) => `${campo}: ${[].concat(msgs).join(" ")}`).join(" | ");
  if (e.code === "throttled" && e.retryAfter) return `Muitas tentativas. Tente de novo em ${e.retryAfter} s.`;
  return e.detail ?? "Algo deu errado.";
}
