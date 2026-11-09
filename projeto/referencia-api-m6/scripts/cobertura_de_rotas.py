import re
from pathlib import Path

import yaml

schema = yaml.safe_load(Path("schema.yml").read_text())
codigo_dos_testes = "\n".join(p.read_text() for p in Path("tests").glob("test_*.py"))

# Cada operação do contrato vira uma expressão: {id} casa com qualquer trecho (f-string ou número)
nao_cobertas = []
total = 0
for caminho, ops in schema["paths"].items():
    padrao = re.escape(caminho).replace(re.escape("{id}"), r"[^\"'?]+")
    for metodo in (m for m in ops if m in ("get", "post", "put", "patch", "delete")):
        total += 1
        # procura uma chamada `.metodo(` na mesma linha de um texto que case com a rota
        achou = any(re.search(rf"\.{metodo}\(\s*f?[\"']{padrao}", linha) for linha in codigo_dos_testes.splitlines())
        if not achou:
            nao_cobertas.append(f"{metodo.upper():<6} {caminho}")

print(f"{total - len(nao_cobertas)}/{total} operações do contrato aparecem em algum teste")
print("sem teste:" if nao_cobertas else "todas cobertas")
for n in nao_cobertas:
    print("  -", n)
