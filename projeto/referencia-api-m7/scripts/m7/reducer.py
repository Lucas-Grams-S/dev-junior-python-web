"""Eventos podem chegar duplicados e FORA DE ORDEM. Um 'redutor' correto dá o MESMO estado final em qualquer ordem."""
import itertools

ORDEM = {"pending": 0, "failed": 1, "paid": 2, "refunded": 3}
TIPO_PARA_ESTADO = {"payment.failed": "failed", "payment.succeeded": "paid", "payment.refunded": "refunded"}


def aplicar(estado_atual, tipo):
    novo = TIPO_PARA_ESTADO[tipo]
    return novo if ORDEM[novo] > ORDEM[estado_atual] else estado_atual        # só ANDA para frente


def reduzir(eventos):
    vistos, estado = set(), "pending"
    for eid, tipo in eventos:
        if eid in vistos:                                                      # duplicata: ignora
            continue
        vistos.add(eid)
        estado = aplicar(estado, tipo)
    return estado


eventos = [("e1", "payment.failed"), ("e2", "payment.succeeded"), ("e3", "payment.refunded")]
finais = {}
for perm in itertools.permutations(eventos):
    finais.setdefault(reduzir(perm), []).append([tipo.split(".")[1] for _, tipo in perm])
print("6 ordens possíveis de chegada → estados finais distintos:", list(finais))
print("exemplo: refunded, failed, succeeded →", reduzir([("e3", "payment.refunded"), ("e1", "payment.failed"), ("e2", "payment.succeeded")]))
print("com duplicatas (e2 chega 3 vezes)    →", reduzir([("e2", "payment.succeeded")] * 3))

# o ERRO clássico: aplicar 'o último que chegou' (sem ordem de estados) depende da ordem
def ingenuo(evs):
    estado = "pending"
    for _, tipo in evs:
        estado = TIPO_PARA_ESTADO[tipo]
    return estado

print("\nredutor ingênuo ('o último vence'):", {ingenuo(p) for p in itertools.permutations(eventos)}, "← depende da ordem: BUG")
