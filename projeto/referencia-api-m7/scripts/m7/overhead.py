"""Processos têm custo: criar, serializar (pickle) e devolver dados. Vale a pena só para trabalho GRANDE."""
import multiprocessing as mp
import pickle
import sys
import time
from concurrent.futures import ProcessPoolExecutor


def quadrado(x):
    return x * x


def pesado(n):
    s = 0
    for i in range(n):
        s += i * i
    return s


def cron(titulo, fn):
    t = time.perf_counter()
    r = fn()
    print(f"  {titulo:<52} {time.perf_counter() - t:6.3f} s")
    return r


if __name__ == "__main__":
    print(f"Python {sys.version.split()[0]} | método de início padrão: {mp.get_start_method()}")
    itens = list(range(20_000))

    print("tarefas MINÚSCULAS (20 mil × x*x)")
    cron("sequencial", lambda: [quadrado(x) for x in itens])
    with ProcessPoolExecutor(4) as ex:
        cron("4 processos, 1 tarefa por vez (chunksize=1)", lambda: list(ex.map(quadrado, itens)))
        cron("4 processos, lotes de 2.500 (chunksize=2500)", lambda: list(ex.map(quadrado, itens, chunksize=2500)))

    print("tarefas GRANDES (4 × laço de 3 milhões)")
    cron("sequencial", lambda: [pesado(3_000_000) for _ in range(4)])
    with ProcessPoolExecutor(4) as ex:
        cron("4 processos", lambda: list(ex.map(pesado, [3_000_000] * 4)))

    print("custo de MOVER dados entre processos (pickle)")
    grande = list(range(3_000_000))
    t = time.perf_counter(); blob = pickle.dumps(grande); t1 = time.perf_counter() - t
    t = time.perf_counter(); pickle.loads(blob); t2 = time.perf_counter() - t
    print(f"  lista de 3 milhões de inteiros: {len(blob) / 1e6:.0f} MB, serializar {t1:.3f} s + desserializar {t2:.3f} s")
