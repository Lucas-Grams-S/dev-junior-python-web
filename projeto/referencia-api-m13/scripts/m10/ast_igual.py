"""Prova de que `ruff format` não muda o PROGRAMA: compara a AST (sem docstrings) de cada arquivo entre dois commits."""
import ast, subprocess, sys
A, B = sys.argv[1], sys.argv[2]
def fonte(rev, arq):
    return subprocess.run(["git", "show", f"{rev}:{arq}"], capture_output=True, text=True).stdout
def limpa(src):
    arv = ast.parse(src)
    for no in ast.walk(arv):
        if isinstance(no, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)) and no.body and isinstance(no.body[0], ast.Expr) \
                and isinstance(getattr(no.body[0], "value", None), ast.Constant) and isinstance(no.body[0].value.value, str):
            no.body = no.body[1:] or [ast.Pass()]
    return ast.dump(arv)
arquivos = subprocess.run(["git", "diff", "--name-only", A, B, "--", "*.py"], capture_output=True, text=True).stdout.split()
iguais = diferentes = 0
for arq in arquivos:
    try:
        ok = limpa(fonte(A, arq)) == limpa(fonte(B, arq))
    except SyntaxError:
        ok = False
    iguais += ok; diferentes += (not ok)
    if not ok: print("  AST DIFERENTE:", arq)
print(f"arquivos alterados: {len(arquivos)} · AST idêntica: {iguais} · AST diferente: {diferentes}")
