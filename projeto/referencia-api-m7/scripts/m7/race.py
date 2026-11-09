"""Condição de corrida: o 'saldo' do estoque atualizado por várias threads, sem e com Lock."""
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor

THREADS, VEZES = 8, 20_000


def sem_trava():
    estoque = {"valor": 0}

    def baixa():
        for _ in range(VEZES):
            estoque["valor"] += 1                 # LER, SOMAR, ESCREVER: três passos, não um

    with ThreadPoolExecutor(THREADS) as ex:
        for _ in range(THREADS):
            ex.submit(baixa)
    return estoque["valor"]


def com_trava():
    estoque = {"valor": 0}
    trava = threading.Lock()

    def baixa():
        for _ in range(VEZES):
            with trava:                           # só uma thread por vez na seção crítica
                estoque["valor"] += 1

    with ThreadPoolExecutor(THREADS) as ex:
        for _ in range(THREADS):
            ex.submit(baixa)
    return estoque["valor"]


def passo_a_passo_sem_trava():
    """A mesma corrida, mas com uma pausa entre ler e escrever, para o problema aparecer sempre."""
    estoque = {"valor": 0}

    def baixa():
        for _ in range(200):
            atual = estoque["valor"]              # 1) ler
            time.sleep(0)                         # 2) outra thread pode entrar aqui
            estoque["valor"] = atual + 1          # 3) escrever (sobrescreve o que outra thread fez)

    with ThreadPoolExecutor(THREADS) as ex:
        for _ in range(THREADS):
            ex.submit(baixa)
    return estoque["valor"]


gil = getattr(sys, "_is_gil_enabled", lambda: True)()
esperado = THREADS * VEZES
print(f"Python {sys.version.split()[0]} | GIL ligado: {gil}")
print(f"esperado: {esperado}")
print(f"sem trava (+= simples)     : {sem_trava()}")
print(f"com Lock                   : {com_trava()}")
print(f"ler → pausar → escrever    : {passo_a_passo_sem_trava()}  (esperado {THREADS * 200})")
