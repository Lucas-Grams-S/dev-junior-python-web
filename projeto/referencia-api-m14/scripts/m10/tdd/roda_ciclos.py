"""Replay da sessão de TDD: para cada ciclo, escreve o teste novo (VERMELHO com o código anterior) e depois o código mínimo (VERDE)."""
import pathlib, re, subprocess, os
LAB = pathlib.Path(os.environ["LAB"]); AQUI = pathlib.Path(__file__).parent
IMPL = LAB / "apps/orders/cupons.py"; TESTE = LAB / "tests/test_cupons.py"
for p in (IMPL, TESTE):
    if p.exists(): p.unlink()

def pytest():
    r = subprocess.run(["uv", "run", "pytest", "-q", "-p", "no:randomly", "-p", "no:cacheprovider", str(TESTE)], cwd=LAB, capture_output=True, text=True, env={**os.environ, "DEBUG": "1"})
    saida = r.stdout
    erros = [l.strip() for l in saida.splitlines() if re.match(r"^E\s+\S", l)]
    final = [l for l in saida.splitlines() if re.search(r"\d+ (passed|failed|error)", l)][-1:]
    return (erros[0][:120] if erros else ""), (final[0] if final else "?")

titulos = {1: "percentual", 2: "triangulação (outro percentual)", 3: "valor fixo", 4: "desconto não passa do subtotal",
           5: "validade (injetando a data)", 6: "valor mínimo e arredondamento"}
teste_acumulado = ""
for n in range(1, 7):
    novo = (AQUI / f"E{n}_teste.py").read_text()
    teste_acumulado += novo if n == 1 else "\n" + novo
    TESTE.write_text(teste_acumulado)
    if n == 1 and IMPL.exists():
        IMPL.unlink()
    erro, resumo = pytest()
    print(f"CICLO {n}: {titulos[n]}")
    print(f"  🔴 VERMELHO: {resumo}" + (f"  ←  {erro}" if erro else ""))
    IMPL.write_text((AQUI / f"E{n}_impl.py").read_text())
    erro, resumo = pytest()
    print(f"  🟢 VERDE   : {resumo}")
