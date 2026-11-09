"""Lint de políticas IAM (aula 13.03): falha com `Action: "*"`, `Resource: "*"` (fora da lista permitida) e NotAction/NotResource.

Não substitui o IAM Access Analyzer (que valida de verdade na AWS), mas pega o erro mais comum antes de aplicar.
Uso: python lint_policy.py arquivo.json [...]
"""

import json
import sys
from pathlib import Path

# ações que NÃO aceitam recurso específico (a própria documentação da AWS manda usar "*")
# (confira cada uma na "Service Authorization Reference" da AWS antes de acrescentar outra à lista)
RESOURCE_STAR_OK = {
    "ecr:GetAuthorizationToken",
    "sts:GetCallerIdentity",
    "ec2:DescribeInstances",  # ações Describe* do EC2 não aceitam recurso específico
    "ssm:GetCommandInvocation",
    "ssm:ListCommandInvocations",
}


def listar(v):
    return v if isinstance(v, list) else [v]


def linta(caminho):
    erros = []
    doc = json.loads(Path(caminho).read_text())
    for i, st in enumerate(listar(doc["Statement"])):
        sid = st.get("Sid", f"#{i}")
        if st.get("Effect") not in ("Allow", "Deny"):
            erros.append(f"{sid}: Effect inválido")
        for chave in ("NotAction", "NotResource"):
            if chave in st:
                erros.append(f"{sid}: evite {chave} (concede tudo MENOS o listado)")
        acoes = listar(st.get("Action", []))
        for a in acoes:
            if a == "*" or a.endswith(":*"):
                erros.append(f"{sid}: ação ampla demais ({a})")
        for r in listar(st.get("Resource", [])):
            if r == "*" and not set(acoes) <= RESOURCE_STAR_OK:
                erros.append(f"{sid}: Resource '*' sem justificativa para {acoes}")
    return erros


if __name__ == "__main__":
    total = 0
    for arq in sys.argv[1:]:
        e = linta(arq)
        print(f"{'OK ' if not e else 'ERRO'} {arq}")
        for m in e:
            print("   -", m)
        total += len(e)
    sys.exit(1 if total else 0)
