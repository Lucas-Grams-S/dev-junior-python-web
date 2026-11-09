class DisjuntorAberto(Exception):
    pass


class Disjuntor:
    """Circuit breaker: depois de N falhas seguidas, para de chamar o serviço por um tempo (fail fast)."""

    def __init__(self, limite=3, recuperacao=10, relogio=None):
        self.limite, self.recuperacao, self.relogio = limite, recuperacao, relogio
        self.falhas, self.aberto_em, self.estado = 0, None, "fechado"

    def chamar(self, fn):
        if self.estado == "aberto":
            if self.relogio() - self.aberto_em < self.recuperacao:
                raise DisjuntorAberto("serviço fora do ar: nem tentei")          # não gasta tempo nem a conexão
            self.estado = "meio-aberto"                                           # deixa passar UMA chamada de teste
        try:
            r = fn()
        except Exception:
            self.falhas += 1
            if self.estado == "meio-aberto" or self.falhas >= self.limite:
                self.estado, self.aberto_em = "aberto", self.relogio()
            raise
        self.falhas, self.estado = 0, "fechado"
        return r


t = [0.0]
saudavel = [False]
chamadas_reais = [0]


def servico():
    chamadas_reais[0] += 1
    if not saudavel[0]:
        raise ConnectionError("503")
    return "ok"


d = Disjuntor(limite=3, recuperacao=10, relogio=lambda: t[0])
for i in range(1, 9):
    try:
        resp = d.chamar(servico)
    except DisjuntorAberto as e:
        resp = f"BLOQUEADA ({e})"
    except ConnectionError:
        resp = "falhou"
    print(f"t={t[0]:4.1f} chamada {i}: {resp:<44} estado={d.estado:<11} chamadas reais ao serviço={chamadas_reais[0]}")
    t[0] += 1
t[0] = 12; saudavel[0] = True
print("--- o serviço voltou e passaram 10 s")
for i in (9, 10):
    resp = d.chamar(servico)
    print(f"t={t[0]:4.1f} chamada {i}: {resp:<44} estado={d.estado:<11} chamadas reais ao serviço={chamadas_reais[0]}")
