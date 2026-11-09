export async function comRetry(fn, {
  tentativas = 4,
  repetivel = (e) => [0, 429, 502, 503, 504].includes(e.status),          // erros transitórios
  atraso = (n, e) => (e.retryAfter ? Number(e.retryAfter) * 1000 : 100 * 2 ** n),   // respeita Retry-After; senão, backoff exponencial
  dormir = (ms) => new Promise((r) => setTimeout(r, ms)),
} = {}) {
  for (let n = 0; ; n++) {
    try {
      return await fn(n);
    } catch (e) {
      if (n + 1 >= tentativas || !repetivel(e)) throw e;
      await dormir(atraso(n, e));
    }
  }
}

// --- demonstração com um relógio falso: nada espera de verdade ---
const esperas = [];
const dormir = async (ms) => { esperas.push(ms); };
const erro = (status, extra = {}) => Object.assign(new Error("falha"), { status, ...extra });

let n = 0;
const r1 = await comRetry(async () => { if (++n < 3) throw erro(503); return "ok"; }, { dormir });
console.log("503, 503, depois sucesso →", r1, "| esperas:", esperas.splice(0));

n = 0;
const r2 = await comRetry(async () => { if (++n < 2) throw erro(429, { retryAfter: "60" }); return "ok"; }, { dormir });
console.log("429 com Retry-After: 60  →", r2, "| esperas:", esperas.splice(0));

n = 0;
try { await comRetry(async () => { n++; throw erro(422); }, { dormir }); } catch (e) { console.log("422 (regra de negócio)   → não repete; tentativas:", n); }

n = 0;
try { await comRetry(async () => { n++; throw erro(0); }, { dormir, tentativas: 3 }); } catch (e) { console.log("rede fora do ar          → desiste após", n, "tentativas | esperas:", esperas.splice(0)); }
