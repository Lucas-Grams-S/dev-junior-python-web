"""Monta o user-data da EC2 a partir do template + compose.prod.yaml + nginx.conf (um arquivo só, sem depender de S3)."""

from pathlib import Path

raiz = Path(__file__).resolve().parents[2]
tpl = (raiz / "deploy/user-data.sh.tpl").read_text()
print(
    tpl.replace("__COMPOSE__", (raiz / "deploy/compose.prod.yaml").read_text().rstrip("\n"))
    .replace("__AWSLOGS__", (raiz / "deploy/compose.awslogs.yaml").read_text().rstrip("\n"))
    .replace("__NGINX__", (raiz / "deploy/nginx.conf").read_text().rstrip("\n"))
    .rstrip("\n")
)
