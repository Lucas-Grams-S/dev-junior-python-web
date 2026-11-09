"""Caça trechos DUPLICADOS (janelas de N linhas iguais, ignorando espaços e comentários). Duplicação é um SINAL, não uma sentença."""
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

LAB = Path(os.environ["LAB"])
JANELA = int(sys.argv[1]) if len(sys.argv) > 1 else 4
alvos = [p for pasta in ("apps", "config", "legado") for p in (LAB / pasta).rglob("*.py") if "migrations" not in p.parts and "__init__" not in p.name]


def normalizar(linha):
    linha = re.sub(r"#.*$", "", linha).strip()
    return re.sub(r"\s+", " ", linha)


janelas = defaultdict(list)
for arq in alvos:
    linhas = [(i + 1, normalizar(l)) for i, l in enumerate(arq.read_text().splitlines())]
    linhas = [(n, l) for n, l in linhas if l and not l.startswith(("import ", "from ", '"""', "@", ")", "]", "}"))]
    for i in range(len(linhas) - JANELA + 1):
        trecho = tuple(l for _, l in linhas[i:i + JANELA])
        if sum(len(l) for l in trecho) > 80:                         # ignora janelas triviais
            janelas[trecho].append((arq.relative_to(LAB), linhas[i][0]))

repetidos = {t: lugares for t, lugares in janelas.items() if len({(a, n // 8) for a, n in lugares}) > 1 and len({a for a, _ in lugares}) >= 1 and len(lugares) > 1}
agrupado = defaultdict(set)
for trecho, lugares in repetidos.items():
    agrupado[tuple(sorted({str(a) for a, _ in lugares}))].add(trecho)
print(f"janela de {JANELA} linhas: {len(repetidos)} trecho(s) repetido(s) em {len(alvos)} arquivos")
vistos = set()
for t, lugares in sorted(repetidos.items(), key=lambda x: -len(x[1])):
    chave = tuple(sorted((str(a), n) for a, n in lugares))
    if any(abs(n - m) < 3 and a == b for (a, n) in chave for (b, m) in vistos):
        continue
    vistos.update(chave)
    print(f"\n● repetido {len(lugares)}× em:", ", ".join(f"{a}:{n}" for a, n in lugares[:4]))
    for l in t[:3]:
        print("     ", l[:100])
    if len(vistos) > 24:
        break
