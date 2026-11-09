import asyncio
import time


async def busca(nome, atraso):
    await asyncio.sleep(atraso)              # ESPERA cooperativa: devolve o controle ao laço de eventos
    return f"{nome} ok"


async def main():
    # 1) chamar uma função async NÃO executa nada: devolve uma corrotina
    c = busca("A", 0.1)
    print("tipo do retorno de busca('A', 0.1):", type(c).__name__)
    print("resultado ao dar await:", await c)

    # 2) em sequência: as esperas se somam
    t = time.perf_counter()
    for n in "ABCDE":
        await busca(n, 0.5)
    print(f"5 awaits seguidos (5 × 0,5 s)        → {time.perf_counter() - t:.2f} s")

    # 3) concorrente: as esperas se sobrepõem
    t = time.perf_counter()
    resultados = await asyncio.gather(*(busca(n, 0.5) for n in "ABCDE"))
    print(f"gather de 5 corrotinas (5 × 0,5 s)   → {time.perf_counter() - t:.2f} s  {resultados}")

    # 4) escala: 10 mil esperas de 1 s ao mesmo tempo, em UMA thread
    t = time.perf_counter()
    await asyncio.gather(*(asyncio.sleep(1) for _ in range(10_000)))
    print(f"gather de 10.000 esperas de 1 s      → {time.perf_counter() - t:.2f} s (uma thread só)")


asyncio.run(main())
