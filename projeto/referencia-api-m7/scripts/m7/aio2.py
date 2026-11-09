"""Bloquear o laço de eventos, semáforo, timeout, cancelamento e TaskGroup."""
import asyncio
import time


async def batimento(lista, ate):
    """Marca o relógio a cada 0,1 s: se o laço travar, aparecem 'buracos' entre as marcas."""
    t0 = time.perf_counter()
    while time.perf_counter() - t0 < ate:
        lista.append(time.perf_counter() - t0)
        await asyncio.sleep(0.1)


def maior_buraco(marcas):
    return max(b - a for a, b in zip(marcas, marcas[1:]))


async def experimento(titulo, trabalho):
    marcas = []
    bat = asyncio.create_task(batimento(marcas, 1.2))
    await asyncio.sleep(0.25)
    await trabalho()
    await bat
    print(f"{titulo:<46} maior intervalo entre batimentos: {maior_buraco(marcas):.2f} s")


async def main():
    print("--- bloquear o laço de eventos")
    async def bloqueia():
        time.sleep(0.6)                                  # ERRADO: chamada bloqueante dentro de async
    async def nao_bloqueia():
        await asyncio.sleep(0.6)                         # certo: espera cooperativa
    async def thread_aparte():
        await asyncio.to_thread(time.sleep, 0.6)         # certo para código bloqueante que você não controla
    await experimento("time.sleep(0.6) dentro de async def", bloqueia)
    await experimento("await asyncio.sleep(0.6)", nao_bloqueia)
    await experimento("await asyncio.to_thread(time.sleep, 0.6)", thread_aparte)

    print("\n--- limitar a concorrência com Semaphore (20 chamadas de 0,2 s)")
    async def chamada(sem, ativos, pico):
        async with sem:
            ativos[0] += 1
            pico[0] = max(pico[0], ativos[0])
            await asyncio.sleep(0.2)
            ativos[0] -= 1
    for limite in (20, 5):
        ativos, pico, sem = [0], [0], asyncio.Semaphore(limite)
        t = time.perf_counter()
        await asyncio.gather(*(chamada(sem, ativos, pico) for _ in range(20)))
        print(f"Semaphore({limite:>2}) → {time.perf_counter() - t:.2f} s | pico simultâneo = {pico[0]}")

    print("\n--- timeout e cancelamento")
    async def lenta():
        try:
            await asyncio.sleep(5)
        except asyncio.CancelledError:
            print("  (a tarefa recebeu o cancelamento e pode limpar recursos)")
            raise
    try:
        async with asyncio.timeout(0.3):
            await lenta()
    except TimeoutError:
        print("asyncio.timeout(0.3) → TimeoutError: a espera foi cancelada")

    print("\n--- gather × TaskGroup quando uma das tarefas falha")
    async def ok(n):
        await asyncio.sleep(0.1 * n)
        return n
    async def falha():
        await asyncio.sleep(0.15)
        raise ValueError("antifraude fora do ar")
    r = await asyncio.gather(ok(1), falha(), ok(2), return_exceptions=True)
    print("gather(return_exceptions=True) →", [repr(x) if isinstance(x, Exception) else x for x in r])
    try:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(ok(1)); tg.create_task(falha()); tg.create_task(ok(5))
    except* ValueError as grupo:
        print("TaskGroup → as irmãs foram canceladas e o erro subiu:", [str(e) for e in grupo.exceptions])


asyncio.run(main())
