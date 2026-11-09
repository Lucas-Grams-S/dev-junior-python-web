"""Procura cadeias if/elif que comparam a MESMA expressão com 3+ constantes: o 'cheiro' do princípio aberto/fechado."""
import ast
import sys
from pathlib import Path

raiz = Path(sys.argv[1])


def cadeia(no):
    """Segue if → elif → elif ...; devolve [(expressao_comparada, constante)]."""
    achados = []
    while isinstance(no, ast.If):
        t = no.test
        if isinstance(t, ast.Compare) and len(t.ops) == 1 and isinstance(t.ops[0], ast.Eq) and isinstance(t.comparators[0], ast.Constant):
            achados.append((ast.unparse(t.left), t.comparators[0].value))
        no = no.orelse[0] if len(no.orelse) == 1 and isinstance(no.orelse[0], ast.If) else None
    return achados


total = 0
for arq in sorted(raiz.rglob("*.py")):
    if "migrations" in arq.parts or ".venv" in arq.parts:
        continue
    arvore = ast.parse(arq.read_text())
    vistos = set()
    for no in ast.walk(arvore):
        if isinstance(no, ast.If) and id(no) not in vistos:
            itens = cadeia(no)
            for filho in ast.walk(no):
                vistos.add(id(filho)) if isinstance(filho, ast.If) and filho is not no and filho in no.orelse else None
            expr = {e for e, _ in itens}
            if len(itens) >= 3 and len(expr) == 1:
                total += 1
                print(f"{arq.relative_to(raiz.parent)}:{no.lineno}  if/elif sobre {expr.pop()!r} com {len(itens)} valores: {[v for _, v in itens]}")
print(f"{total} cadeia(s) suspeita(s)")
