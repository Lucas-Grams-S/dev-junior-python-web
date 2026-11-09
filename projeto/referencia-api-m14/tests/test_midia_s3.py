"""Mídia dos produtos (aula 13.06): upload validado, armazenamento em disco OU S3 (simulado pelo moto, sem rede e sem conta AWS)."""

import io

import boto3
import pytest
from moto import mock_aws
from PIL import Image

from apps.catalog.models import Product

BUCKET = "minishop-midia-teste"
REGIAO = "sa-east-1"


def imagem(formato="PNG", tamanho=(8, 8)):
    buf = io.BytesIO()
    Image.new("RGB", tamanho, "red").save(buf, formato)
    buf.seek(0)
    buf.name = f"foto.{formato.lower()}"
    return buf


@pytest.fixture
def produto(seed):
    return Product.objects.get(sku="AUD-001") if Product.objects.filter(sku="AUD-001").exists() else Product.objects.first()


@pytest.fixture
def disco(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    return tmp_path


@pytest.fixture
def s3(settings, monkeypatch):
    """Um S3 de mentira (moto) com um bucket privado, e o Django apontado para ele."""
    for k in ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"):
        monkeypatch.setenv(k, "teste")  # credenciais FALSAS: o moto não valida
    with mock_aws():
        cliente = boto3.client("s3", region_name=REGIAO)
        cliente.create_bucket(Bucket=BUCKET, CreateBucketConfiguration={"LocationConstraint": REGIAO})
        settings.STORAGES = {
            **settings.STORAGES,
            "default": {
                "BACKEND": "storages.backends.s3.S3Storage",
                "OPTIONS": {
                    "bucket_name": BUCKET,
                    "region_name": REGIAO,
                    "signature_version": "s3v4",
                    "default_acl": None,
                    "querystring_auth": True,
                    "querystring_expire": 600,
                    "file_overwrite": False,
                },
            },
        }
        yield cliente


def chaves(cliente):
    return [o["Key"] for o in cliente.list_objects_v2(Bucket=BUCKET).get("Contents", [])]


def test_upload_em_disco(api_as, produto, disco):
    r = api_as("gerente").post(f"/api/v1/products/{produto.pk}/image/", {"image": imagem()}, format="multipart")
    assert r.status_code == 200, r.content
    assert r.json()["image_url"].startswith("/media/products/")
    assert list((disco / "products").iterdir())  # o arquivo existe de verdade


def test_upload_no_s3_privado_com_url_assinada(api_as, produto, s3):
    r = api_as("gerente").post(f"/api/v1/products/{produto.pk}/image/", {"image": imagem()}, format="multipart")
    assert r.status_code == 200, r.content
    assert len(chaves(s3)) == 1 and chaves(s3)[0].startswith("products/")
    url = r.json()["image_url"]
    assert "X-Amz-Signature" in url and "X-Amz-Expires=600" in url  # temporária e assinada
    acl = s3.get_object_acl(Bucket=BUCKET, Key=chaves(s3)[0])
    assert not any(g["Grantee"].get("URI", "").endswith("AllUsers") for g in acl["Grants"])  # nada público


def test_substituir_e_remover_nao_deixam_orfaos(api_as, produto, s3):
    gerente = api_as("gerente")
    gerente.post(f"/api/v1/products/{produto.pk}/image/", {"image": imagem()}, format="multipart")
    gerente.post(f"/api/v1/products/{produto.pk}/image/", {"image": imagem("JPEG")}, format="multipart")
    assert len(chaves(s3)) == 1
    assert gerente.delete(f"/api/v1/products/{produto.pk}/image/").status_code == 204
    assert chaves(s3) == []


@pytest.mark.parametrize("papel", [None, "cliente"])
def test_so_quem_pode_alterar_produto_envia_imagem(api_as, produto, disco, papel):
    r = api_as(papel).post(f"/api/v1/products/{produto.pk}/image/", {"image": imagem()}, format="multipart")
    assert r.status_code in (401, 403)
    assert not (disco / "products").exists()


def test_rejeita_texto_disfarçado_gif_e_arquivo_grande(api_as, produto, disco):
    gerente = api_as("gerente")
    falso = io.BytesIO(b"<?php echo 1; ?>")
    falso.name = "foto.png"
    assert gerente.post(f"/api/v1/products/{produto.pk}/image/", {"image": falso}, format="multipart").status_code == 400
    assert gerente.post(f"/api/v1/products/{produto.pk}/image/", {"image": imagem("GIF")}, format="multipart").status_code == 400
    grande = io.BytesIO()
    Image.effect_noise((1500, 1500), 200).convert("RGB").save(grande, "PNG")
    grande.seek(0)
    grande.name = "grande.png"
    assert grande.getbuffer().nbytes > 2 * 1024 * 1024
    assert gerente.post(f"/api/v1/products/{produto.pk}/image/", {"image": grande}, format="multipart").status_code == 400
    assert not (disco / "products").exists()


def test_produto_sem_imagem_devolve_null(api_as, produto):
    assert api_as(None).get(f"/api/v1/products/{produto.pk}/").json()["image_url"] is None
