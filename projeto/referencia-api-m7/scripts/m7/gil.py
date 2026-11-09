"""Threads × processos, para trabalho de ESPERA e de CÁLCULO. Rode no Python normal e no free-threaded."""
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor

N = 4                                    # número de tarefas (e de workers)


def espera(_):                           # I/O-bound simulado
    time.sleep(0.5)


def calcula(_):                          # CPU-bound: laço Python puro
    s = 0
    for i in range(6_000_000):
        s += i * i
    return s


def cronometrar(titulo, fn):
    t = time.perf_counter()
    fn()
    print(f"  {titulo:<34} {time.perf_counter() - t:5.2f} s")


def sequencial(f):
    return lambda: [f(i) for i in range(N)]


def com_threads(f):
    def run():
        with ThreadPoolExecutor(N) as ex:
            list(ex.map(f, range(N)))
    return run


def com_processos(f):
    def run():
        with ProcessPoolExecutor(N) as ex:
            list(ex.map(f, range(N)))
    return run


if __name__ == "__main__":
    gil = getattr(sys, "_is_gil_enabled", lambda: True)()
    print(f"Python {sys.version.split()[0]} | GIL ligado: {gil} | núcleos: {os.cpu_count()}")
    print("ESPERA (4 × sleep 0,5 s)")
    cronometrar("sequencial", sequencial(espera))
    cronometrar("4 threads", com_threads(espera))
    cronometrar("4 processos", com_processos(espera))
    print("CÁLCULO (4 × laço de 6 milhões)")
    cronometrar("sequencial", sequencial(calcula))
    cronometrar("4 threads", com_threads(calcula))
    cronometrar("4 processos", com_processos(calcula))
