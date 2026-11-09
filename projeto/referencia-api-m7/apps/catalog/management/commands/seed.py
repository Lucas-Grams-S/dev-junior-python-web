from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand

from apps.catalog.models import Category, Product

CATEGORIAS = {"informatica": ("Informática", ["Notebook", "Mouse", "Teclado", "Monitor", "Webcam", "Hub USB"]),
              "audio": ("Áudio", ["Fone de ouvido", "Caixa de som", "Microfone", "Headset", "Interface de áudio"]),
              "casa": ("Casa", ["Luminária", "Cadeira", "Mesa", "Suporte de monitor", "Organizador de cabos"])}


class Command(BaseCommand):
    def handle(self, *a, **o):
        cats, n = {}, 0
        for slug, (nome, _) in CATEGORIAS.items():
            cats[slug], _ = Category.objects.update_or_create(slug=slug, defaults={"name": nome})
        for slug, (_, bases) in CATEGORIAS.items():
            for base in bases:
                for v in ["Básico", "Plus", "Pro", "Max"]:
                    n += 1
                    Product.objects.get_or_create(sku=f"{slug[:3].upper()}-{n:03}", defaults={
                        "category": cats[slug], "name": f"{base} {v}", "description": f"{base}, versão {v}.",
                        "price": Decimal(2990 + (n * 1370) % 150000) / 100, "stock": 5 + (n * 7) % 40, "is_active": n % 17 != 0})
        U = get_user_model()
        for username, grupo, staff in [("gerente", "Gerente", True), ("estoquista", "Estoquista", True), ("cliente", None, False)]:
            u, novo = U.objects.get_or_create(username=username, defaults={"email": f"{username}@minishop.local", "is_staff": staff})
            if novo:
                u.set_password("dev-somente-local-123"); u.save()
            if grupo:
                u.groups.add(Group.objects.get(name=grupo))
        self.stdout.write(f"Seed ok: {Product.objects.count()} produtos")
