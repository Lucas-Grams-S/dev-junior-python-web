import asyncio
import random
import time


async def pontuar(pedido_id, atraso=0.3):
    async with asyncio.timeout(1):
        await asyncio.sleep(atraso)                       # no real: await cliente.get(...) (aula 04)
        return pedido_id, random.randint(0, 100)


async def pontuar_varios(ids, limite=5):
    sem = asyncio.Semaphore(limite)
    resultados = {}

    async def um(i):
        async with sem:
            try:
                resultados[i] = (await pontuar(i))[1]
            except TimeoutError:
                resultados[i] = None                       # "desconhecida": o pedido segue para revisão manual

    async with asyncio.TaskGroup() as tg:
        for i in ids:
            tg.create_task(um(i))
    return resultados


t = time.perf_counter()
r = asyncio.run(pontuar_varios(range(10)))
print(f"{len(r)} pedidos em {time.perf_counter() - t:.2f} s (limite 5 → 2 rodadas de 0,3 s)")
