outbox = [{"id": i, "publicado": False} for i in (1, 2, 3)]
broker, vistos, efeitos = [], set(), []


def rele(cair_no_evento=None):
    for ev in outbox:
        if ev["publicado"]:
            continue
        broker.append(ev["id"])                                    # 1) publica
        if ev["id"] == cair_no_evento:
            raise RuntimeError(f"relé caiu depois de publicar o evento {ev['id']} e antes de marcar")
        ev["publicado"] = True                                     # 2) marca


def consumidor():
    while broker:
        mid = broker.pop(0)
        if mid in vistos:                                          # idempotência
            continue
        vistos.add(mid)
        efeitos.append(mid)


try:
    rele(cair_no_evento=2)
except RuntimeError as e:
    print(e)
print("no broker depois da queda:", broker, "| pendentes:", [e["id"] for e in outbox if not e["publicado"]])
rele()                                                              # o relé reinicia e retoma
print("no broker depois do 2º relé:", broker, "(o evento 2 aparece DUAS vezes)")
consumidor()
print("efeitos aplicados:", efeitos, "→ um por evento, nenhuma perda")
