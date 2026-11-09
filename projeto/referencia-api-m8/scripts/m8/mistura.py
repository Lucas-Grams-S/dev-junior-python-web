"""Detecta quantas 'camadas' uma função mistura, procurando sinais no código (AST). É uma heurística didática, não um linter completo."""
import ast
import inspect
import os
import sys
from pathlib import Path

LAB = Path(os.environ["LAB"])
sys.path.insert(0, str(LAB))
os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"
import django

django.setup()

SINAIS = {
    "interface (HTTP)": {"request", "Response", "HttpResponse", "JsonResponse", "status", "render", "redirect", "ValidationError"},
    "dados (banco)": {"objects", "cursor", "execute", "save", "select_for_update", "update", "filter", "get", "create", "delete", "fetchone"},
    "infraestrutura": {"send_mail", "httpx", "requests", "print", "open", "sleep", "delay", "get_channel_layer", "logger"},
}


def camadas_de(funcao):
    arvore = ast.parse(inspect.getsource(funcao).lstrip() if inspect.getsource(funcao)[0] != " " else __import__("textwrap").dedent(inspect.getsource(funcao)))
    nomes = {n.id for n in ast.walk(arvore) if isinstance(n, ast.Name)} | {n.attr for n in ast.walk(arvore) if isinstance(n, ast.Attribute)}
    achadas = {camada: sorted(nomes & sinais) for camada, sinais in SINAIS.items() if nomes & sinais}
    ifs = sum(isinstance(n, (ast.If, ast.For, ast.While, ast.BoolOp)) for n in ast.walk(arvore))
    return achadas, ifs


from apps.orders import services as svc_pedidos
from apps.orders.api import OrderViewSet
from apps.payments import services as svc_pagamentos
from legado.pedidos_legado import processar_pedido

for nome, fn in [("legado.processar_pedido", processar_pedido), ("orders.services.create_order", svc_pedidos.create_order),
                 ("payments.services.processar_evento", svc_pagamentos.processar_evento),
                 ("orders.api.OrderViewSet.create", OrderViewSet.create), ("orders.api.OrderViewSet.get_queryset", OrderViewSet.get_queryset)]:
    achadas, ramos = camadas_de(fn)
    print(f"{nome:<38} mistura {len(achadas)} camada(s) | ramos/decisões: {ramos:>2}")
    for camada, sinais in achadas.items():
        print(f"    · {camada:<18} {', '.join(sinais)}")
