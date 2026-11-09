import heapq
import itertools
import time


class Loop:
    """Um laço de eventos de brinquedo: corrotinas são GERADORES que dão `yield` quando querem esperar."""

    def __init__(self):
        self.prontas, self.dormindo = [], []                 # fila de prontas e heap de (acordar_em, id, tarefa)
        self.contador = itertools.count()

    def criar(self, gen, nome):
        self.prontas.append((nome, gen))

    def rodar(self):
        while self.prontas or self.dormindo:
            while self.dormindo and self.dormindo[0][0] <= time.perf_counter():
                _, _, tarefa = heapq.heappop(self.dormindo)
                self.prontas.append(tarefa)                  # acordou: volta para a fila de prontas
            if not self.prontas:
                time.sleep(max(0, self.dormindo[0][0] - time.perf_counter()))   # nada a fazer: dorme até o próximo despertar
                continue
            nome, gen = self.prontas.pop(0)
            try:
                segundos = next(gen)                         # roda a tarefa até o próximo yield
            except StopIteration:
                continue                                     # terminou
            heapq.heappush(self.dormindo, (time.perf_counter() + segundos, next(self.contador), (nome, gen)))


t0 = time.perf_counter()
def log(msg):
    print(f"[{time.perf_counter() - t0:4.2f} s] {msg}")


def pedido(nome, passos):
    for n, (descricao, espera) in enumerate(passos, 1):
        log(f"{nome}: {descricao}")
        yield espera                                         # "me acorde daqui a `espera` segundos" (= await sleep)
    log(f"{nome}: concluído")


loop = Loop()
loop.criar(pedido("A", [("grava no banco", 0.1), ("manda e-mail", 0.4)]), "A")
loop.criar(pedido("B", [("grava no banco", 0.1), ("consulta antifraude", 0.3)]), "B")
loop.criar(pedido("C", [("grava no banco", 0.1)]), "C")
loop.rodar()
print(f"total: {time.perf_counter() - t0:.2f} s (sequencial seria 1,0 s) — UMA thread, três pedidos intercalados")
