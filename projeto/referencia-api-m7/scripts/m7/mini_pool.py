import queue
import threading
import time


class MiniPool:
    """Pool de threads feito à mão: uma fila de tarefas, N workers e uma 'pílula de veneno' para encerrar."""

    def __init__(self, n):
        self.tarefas, self.resultados = queue.Queue(), queue.Queue()
        self.ativos, self.pico = 0, 0
        self.trava = threading.Lock()
        self.workers = [threading.Thread(target=self._loop, daemon=True) for _ in range(n)]
        for w in self.workers:
            w.start()

    def _loop(self):
        while True:
            item = self.tarefas.get()
            if item is None:                               # pílula de veneno: encerra este worker
                return
            indice, fn, arg = item
            with self.trava:
                self.ativos += 1
                self.pico = max(self.pico, self.ativos)
            try:
                self.resultados.put((indice, fn(arg)))
            finally:
                with self.trava:
                    self.ativos -= 1

    def map(self, fn, itens):
        itens = list(itens)
        for i, x in enumerate(itens):
            self.tarefas.put((i, fn, x))
        saida = [None] * len(itens)
        for _ in itens:
            i, r = self.resultados.get()
            saida[i] = r                                   # devolve na ORDEM de entrada
        for _ in self.workers:
            self.tarefas.put(None)
        for w in self.workers:
            w.join()
        return saida


def lenta(x):
    time.sleep(0.2)
    return x * x


t = time.perf_counter()
pool = MiniPool(4)
print("resultados:", pool.map(lenta, range(12)))
print(f"12 tarefas de 0,2 s com 4 workers: {time.perf_counter() - t:.2f} s (sequencial seria 2,4 s) | pico de tarefas simultâneas: {pool.pico}")
