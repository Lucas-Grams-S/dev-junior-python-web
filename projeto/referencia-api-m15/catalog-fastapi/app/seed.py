"""Seed IDÊNTICO ao do Django (mesmos SKUs, preços, estoques): permite comparar as duas APIs lado a lado."""

import asyncio
from decimal import Decimal

from sqlalchemy import select

from .db import SessionLocal
from .models import Category, Product
from .slug import slugify

CATEGORIAS = {
    "informatica": ("Informática", ["Notebook", "Mouse", "Teclado", "Monitor", "Webcam", "Hub USB"]),
    "audio": ("Áudio", ["Fone de ouvido", "Caixa de som", "Microfone", "Headset", "Interface de áudio"]),
    "casa": ("Casa", ["Luminária", "Cadeira", "Mesa", "Suporte de monitor", "Organizador de cabos"]),
}


async def seed() -> int:
    async with SessionLocal() as s:
        cats = {}
        for slug, (nome, _) in CATEGORIAS.items():
            c = await s.scalar(select(Category).where(Category.slug == slug)) or Category(slug=slug, name=nome)
            s.add(c)
            cats[slug] = c
        await s.flush()
        n = 0
        for slug, (_, bases) in CATEGORIAS.items():
            for base in bases:
                for v in ["Básico", "Plus", "Pro", "Max"]:
                    n += 1
                    sku = f"{slug[:3].upper()}-{n:03}"
                    if await s.scalar(select(Product.id).where(Product.sku == sku)):
                        continue
                    nome = f"{base} {v}"
                    s.add(
                        Product(
                            category=cats[slug],
                            sku=sku,
                            name=nome,
                            slug=slugify(nome),
                            description=f"{base}, versão {v}.",
                            price=Decimal(2990 + (n * 1370) % 150000) / 100,
                            stock=5 + (n * 7) % 40,
                            is_active=n % 17 != 0,
                        )
                    )
        await s.commit()
        return len((await s.scalars(select(Product.id))).all())


if __name__ == "__main__":
    print(f"Seed ok: {asyncio.run(seed())} produtos")
