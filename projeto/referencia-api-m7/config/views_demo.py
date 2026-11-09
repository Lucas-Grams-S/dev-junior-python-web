import asyncio
import time

from django.http import JsonResponse


def espera_sync(request):                       # view SÍNCRONA que espera 0,5 s (como uma chamada a API externa)
    time.sleep(0.5)
    return JsonResponse({"tipo": "sync"})


async def espera_async(request):                # view ASSÍNCRONA que espera 0,5 s sem bloquear o laço
    await asyncio.sleep(0.5)
    return JsonResponse({"tipo": "async"})
