"""Mapa de dependências do MiniShop: quem importa quem, por camada (usando `grimp`, a base do import-linter)."""
import os
import sys
from collections import defaultdict
from pathlib import Path

import grimp

LAB = Path(os.environ["LAB"])
sys.path.insert(0, str(LAB))

graph = grimp.build_graph("apps", "config", include_external_packages=True)

CAMADAS = {"api": "interface", "serializers": "interface", "filters": "interface", "permissions": "interface", "throttles": "interface",
           "consumers": "interface", "routing": "interface", "auth": "interface",
           "services": "serviços", "tasks": "serviços", "notifications": "serviços", "outbox": "serviços", "security": "serviços",
           "models": "dados"}


def camada(modulo):
    partes = modulo.split(".")
    return CAMADAS.get(partes[-1], "outro") if partes[0] == "apps" and len(partes) >= 3 else None


def app(modulo):
    p = modulo.split(".")
    return p[1] if p[0] == "apps" and len(p) > 1 else None


arestas = defaultdict(set)
for m in sorted(graph.modules):
    if camada(m) is None:
        continue
    for dep in graph.find_modules_directly_imported_by(m):
        c = camada(dep)
        if c:
            arestas[(camada(m), c)].add((m, dep))
print("dependências entre camadas (origem → destino): número de imports")
for (a, b), itens in sorted(arestas.items()):
    print(f"  {a:<10} → {b:<10} {len(itens):>3}")

print("\nregras que a arquitetura em camadas quer garantir:")
violacoes = []
for m in sorted(graph.modules):
    c = camada(m)
    if c is None:
        continue
    for dep in sorted(graph.find_modules_directly_imported_by(m)):
        raiz = dep.split(".")[0]
        if c in ("serviços", "dados") and raiz in ("rest_framework", "channels"):
            violacoes.append((m, dep, "R1: serviços/dados não devem depender de framework de interface (DRF/Channels)"))
        if c == "dados" and camada(dep) in ("serviços", "interface"):
            violacoes.append((m, dep, "R2: modelos não importam serviços nem interface"))
        if c == "serviços" and camada(dep) == "interface":
            violacoes.append((m, dep, "R3: serviços não importam a camada de interface"))
for m, dep, regra in violacoes:
    print(f"  ✘ {m}  →  {dep}\n      {regra}")
if not violacoes:
    print("  (nenhuma violação)")

print("\ndependências entre APPS (quem usa quem):")
entre = defaultdict(set)
for m in graph.modules:
    a = app(m)
    if not a:
        continue
    for dep in graph.find_modules_directly_imported_by(m):
        b = app(dep)
        if b and b != a:
            entre[a].add(b)
for a in sorted(entre):
    print(f"  {a:<9} → {', '.join(sorted(entre[a]))}")
