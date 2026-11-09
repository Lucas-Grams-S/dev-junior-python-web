class Reclamos:
    """Consumidor idempotente com 'reclamo' (lease): quem reclama a mensagem tem prazo para terminar; se sumir, outro assume."""

    def __init__(self, prazo, relogio):
        self.prazo, self.relogio, self.estado = prazo, relogio, {}      # id -> {"status", "desde", "dono"}

    def reclamar(self, mid, worker):
        reg = self.estado.get(mid)
        agora = self.relogio()
        if reg is None or reg["status"] == "livre" or (reg["status"] == "reclamado" and agora - reg["desde"] >= self.prazo):
            self.estado[mid] = {"status": "reclamado", "desde": agora, "dono": worker}      # este worker pode agir
            return True
        return False                                                    # já feita, ou outro worker está com ela

    def concluir(self, mid, worker):
        if self.estado.get(mid, {}).get("dono") == worker:
            self.estado[mid]["status"] = "feito"

    def soltar(self, mid, worker):                                      # falha transitória: devolve para tentar de novo
        if self.estado.get(mid, {}).get("dono") == worker:
            self.estado[mid]["status"] = "livre"


t = [0]
r = Reclamos(prazo=10, relogio=lambda: t[0])
efeitos = []


def processar(worker, mid, cai=False, falha=False):
    if not r.reclamar(mid, worker):
        print(f"t={t[0]:>2} {worker}: mensagem {mid} → ignorada (já feita ou com outro worker)")
        return
    if cai:
        print(f"t={t[0]:>2} {worker}: reclamou {mid} e CAIU no meio (sem concluir nem soltar)")
        return
    if falha:
        r.soltar(mid, worker)
        print(f"t={t[0]:>2} {worker}: falha transitória em {mid} → soltou o reclamo para a próxima tentativa")
        return
    efeitos.append((worker, mid))
    r.concluir(mid, worker)
    print(f"t={t[0]:>2} {worker}: processou {mid} (efeito aplicado) e concluiu")


processar("A", "m1")                      # normal
processar("B", "m1")                      # duplicata da mesma mensagem
processar("A", "m2", falha=True)          # falha transitória
processar("B", "m2")                      # a nova tentativa funciona
processar("A", "m3", cai=True)            # A morre com m3 reclamada
t[0] = 4;  processar("B", "m3")           # cedo demais: o reclamo de A ainda vale
t[0] = 11; processar("B", "m3")           # reclamo expirou: B assume
print("efeitos aplicados:", efeitos, "→ cada mensagem teve efeito exatamente UMA vez")
