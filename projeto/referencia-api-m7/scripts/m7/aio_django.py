"""Django + asyncio: o ORM síncrono é proibido dentro do laço de eventos; use a API assíncrona ou sync_to_async."""
import asyncio

from asgiref.sync import sync_to_async
from django.core.exceptions import SynchronousOnlyOperation

from apps.cart import services as carrinho
from apps.catalog.models import Product


async def main():
    try:
        Product.objects.count()                               # ORM síncrono dentro de async def
    except SynchronousOnlyOperation as e:
        print("ORM síncrono em async →", type(e).__name__, "|", str(e)[:70], "…")

    print("acount()            →", await Product.objects.acount())
    p = await Product.objects.aget(sku="INF-002")
    print("aget()              →", p.sku, p.name)
    nomes = [x.name async for x in Product.objects.filter(is_active=True).order_by("name")[:3]]
    print("async for           →", nomes)
    print("aexists()           →", await Product.objects.filter(sku="NAO-EXISTE").aexists())

    # um serviço síncrono (transação, travas) chamado a partir de código async:
    from django.contrib.auth import get_user_model
    usuario = await get_user_model().objects.aget(username="cliente")
    cart = await sync_to_async(carrinho.get_cart)(usuario)
    print("sync_to_async       → carrinho", cart.pk, "do usuário", usuario.username)

    # várias consultas independentes ao mesmo tempo
    total, ativos, categorias = await asyncio.gather(
        Product.objects.acount(),
        Product.objects.filter(is_active=True).acount(),
        sync_to_async(lambda: list(Product.objects.order_by("category__name").values_list("category__name", flat=True).distinct()))(),
    )
    print("gather de 3 consultas →", total, "produtos,", ativos, "ativos,", len(categorias), "categorias")


asyncio.run(main())
