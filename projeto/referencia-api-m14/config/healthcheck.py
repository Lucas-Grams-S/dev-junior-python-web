"""Sonda do Docker (HEALTHCHECK): sai com 0 se o Django responde, 1 se não.

Roda DENTRO do container, só com a biblioteca padrão (a imagem não tem curl).
Consulta /health/ready/ (aula 14.01): responde 200 só se o banco e o cache respondem.
"""

import os
import sys
import urllib.request

host = os.environ.get("HEALTHCHECK_HOST") or os.environ.get("ALLOWED_HOSTS", "localhost").split(",")[0]
requisicao = urllib.request.Request(
    "http://127.0.0.1:8000/health/ready/",
    headers={"Host": host},  # as sondas estão em SECURE_REDIRECT_EXEMPT: não precisam falar HTTPS
)
try:
    sys.exit(0 if urllib.request.urlopen(requisicao, timeout=3).status == 200 else 1)  # noqa: S310  (URL fixa em http://127.0.0.1)
except Exception as erro:  # qualquer falha = não saudável
    print(f"healthcheck falhou: {erro}", file=sys.stderr)
    sys.exit(1)
