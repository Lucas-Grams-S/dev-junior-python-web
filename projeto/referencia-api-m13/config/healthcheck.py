"""Sonda do Docker (HEALTHCHECK): sai com 0 se o Django responde, 1 se não.

Roda DENTRO do container, só com a biblioteca padrão (a imagem não tem curl).
O endpoint /health/ de verdade (banco, cache) é do módulo 14; aqui usamos a página de login do Admin.
"""

import os
import sys
import urllib.request

host = os.environ.get("HEALTHCHECK_HOST") or os.environ.get("ALLOWED_HOSTS", "localhost").split(",")[0]
requisicao = urllib.request.Request(
    "http://127.0.0.1:8000/admin/login/",
    headers={"Host": host, "X-Forwarded-Proto": "https"},  # com o cabeçalho, SECURE_SSL_REDIRECT não redireciona
)
try:
    sys.exit(0 if urllib.request.urlopen(requisicao, timeout=3).status == 200 else 1)  # noqa: S310  (URL fixa em http://127.0.0.1)
except Exception as erro:  # qualquer falha = não saudável
    print(f"healthcheck falhou: {erro}", file=sys.stderr)
    sys.exit(1)
