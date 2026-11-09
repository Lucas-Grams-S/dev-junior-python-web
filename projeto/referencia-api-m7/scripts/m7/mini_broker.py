import collections
import itertools


class MiniBroker:
    """Fila com 'ack' e prazo de visibilidade: mensagem reservada e NÃO confirmada volta para a fila (entrega at-least-once)."""

    def __init__(self, prazo, relogio):
        self.prazo, self.relogio = prazo, relogio
        self.fila = collections.deque()
        self.reservadas = {}                                  # id -> (mensagem, reservada_em, worker)
        self.ids = itertools.count(1)

    def publicar(self, corpo):
        self.fila.append((next(self.ids), corpo))

    def _devolver_vencidas(self):
        for mid, (msg, em, worker) in list(self.reservadas.items()):
            if self.relogio() - em >= self.prazo:
                del self.reservadas[mid]
                self.fila.appendleft(msg)                      # visível de novo: outro worker pode pegar
                print(f"    [broker t={self.relogio():>2}] mensagem {mid} não foi confirmada por {worker}: volta para a fila")

    def reservar(self, worker):
        self._devolver_vencidas()
        if not self.fila:
            return None
        msg = self.fila.popleft()
        self.reservadas[msg[0]] = (msg, self.relogio(), worker)
        return msg

    def ack(self, mid):
        self.reservadas.pop(mid, None)                         # confirmada: some de vez


t = [0]
broker = MiniBroker(prazo=5, relogio=lambda: t[0])
efeitos = []                                                   # o que realmente aconteceu no "mundo" (e-mails enviados)

broker.publicar({"enviar_email": "pedido #7"})

print("t=0  worker A reserva e ENVIA o e-mail...")
mid, corpo = broker.reservar("A")
efeitos.append(f"e-mail do {corpo['enviar_email']} enviado por A")
print("     ...mas A cai (kill -9, falta de memória) ANTES de confirmar (ack).")

t[0] = 3; print("t=3  worker B pede trabalho:", broker.reservar("B"), "(a mensagem de A ainda está reservada)")
t[0] = 6
print("t=6  worker B pede trabalho de novo:")
mid2, corpo2 = broker.reservar("B")
efeitos.append(f"e-mail do {corpo2['enviar_email']} enviado por B")
broker.ack(mid2)
print("\nefeitos no mundo real:")
for e in efeitos:
    print("  ·", e)
print(f"→ mensagem entregue {len(efeitos)} vezes: at-least-once. A tarefa precisa ser IDEMPOTENTE (aula 7.07).")
