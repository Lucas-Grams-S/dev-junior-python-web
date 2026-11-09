"""Esvazia um bucket INCLUSIVE versões e marcadores de exclusão (o `aws s3 rb --force` NÃO apaga versões: aula 13.06/13.08).

Uso: uv run python scripts/aws/empty_bucket.py NOME_DO_BUCKET
Respeita AWS_ENDPOINT_URL (simulador) e as credenciais da cadeia padrão do boto3. Não falha se o bucket não existir.
"""

import sys

import boto3
from botocore.exceptions import ClientError

nome = sys.argv[1]
bucket = boto3.resource("s3").Bucket(nome)
try:
    apagados = bucket.object_versions.delete()  # remove versões e delete markers, em lotes de 1000
    total = sum(len(r.get("Deleted", [])) for r in apagados)
    print(f"   {total} versão(ões)/objeto(s) removido(s) de {nome}")
except ClientError as erro:
    if erro.response["Error"]["Code"] in ("NoSuchBucket", "404"):
        print(f"   (bucket {nome} não existe)")
    else:
        raise
