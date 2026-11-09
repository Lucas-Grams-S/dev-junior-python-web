import pytest

URL = "/api/v1/products/"
NOVO = {"sku": "inf-900", "name": "Nobreak Pro", "price": "399.90", "stock": 3, "category_slug": "informatica"}


async def test_lista_paginada_so_ativos(client):
    r = await client.get(URL)
    assert r.status_code == 200
    j = r.json()
    assert set(j) == {"count", "next", "previous", "results"}
    assert len(j["results"]) == 20
    assert j["previous"] is None and j["next"].endswith("page=2")
    assert all(p["is_active"] for p in j["results"])
    assert j["count"] == 64 - 3  # 64 produtos; n % 17 == 0 -> 17, 34, 51 inativos


async def test_equipe_ve_inativos(client, auth):
    j = (await client.get(URL, headers=auth)).json()
    assert j["count"] == 64


async def test_token_errado_nao_vira_equipe(client):
    j = (await client.get(URL, headers={"Authorization": "Bearer errado"})).json()
    assert j["count"] == 61


async def test_formato_do_produto(client):
    p = (await client.get(URL)).json()["results"][0]
    assert set(p) == {"id", "sku", "name", "slug", "description", "price", "stock", "in_stock", "is_active", "category", "created_at"}
    assert isinstance(p["price"], str)  # Decimal vira texto no JSON: sem erro de ponto flutuante
    assert set(p["category"]) == {"id", "name", "slug"}


@pytest.mark.parametrize(
    ("query", "confere"),
    [
        ("category=audio", lambda p: p["category"]["slug"] == "audio"),
        ("price_min=500&price_max=900", lambda p: 500 <= float(p["price"]) <= 900),
        ("in_stock=true", lambda p: p["stock"] > 0),
        ("search=mouse", lambda p: "mouse" in p["name"].lower()),
    ],
)
async def test_filtros(client, query, confere):
    j = (await client.get(f"{URL}?{query}&page_size=100")).json()
    assert j["results"] and all(confere(p) for p in j["results"])


async def test_ordenacao_e_lista_permitida(client):
    precos = [float(p["price"]) for p in (await client.get(f"{URL}?ordering=-price")).json()["results"]]
    assert precos == sorted(precos, reverse=True)
    assert (await client.get(f"{URL}?ordering=password")).status_code == 400


async def test_page_size_limitado_ao_maximo(client):
    assert len((await client.get(f"{URL}?page_size=1000")).json()["results"]) == 61
    assert (await client.get(f"{URL}?page=0")).status_code == 422


async def test_detalhe_e_404(client):
    assert (await client.get(f"{URL}1/")).status_code == 200
    assert (await client.get(f"{URL}999999/")).status_code == 404
    assert (await client.get(f"{URL}abc/")).status_code == 422  # tipo errado na URL, validado pelo int


async def test_inativo_404_para_publico(client, auth):
    assert (await client.get(f"{URL}17/")).status_code == 404
    assert (await client.get(f"{URL}17/", headers=auth)).status_code == 200


async def test_criar_exige_token(client, auth):
    assert (await client.post(URL, json=NOVO)).status_code == 401
    r = await client.post(URL, json=NOVO, headers=auth)
    assert r.status_code == 201, r.text
    j = r.json()
    assert j["sku"] == "INF-900" and j["slug"] == "nobreak-pro" and j["in_stock"] is True
    assert r.headers["location"] == f"/api/v1/products/{j['id']}/"
    assert (await client.get(f"{URL}{j['id']}/")).json()["name"] == "Nobreak Pro"


async def test_escrita_fechada_sem_token_configurado(client, auth, monkeypatch):
    monkeypatch.setattr("app.security.settings.api_token", "")
    assert (await client.post(URL, json=NOVO, headers={"Authorization": "Bearer "})).status_code in (401, 403)
    assert (await client.post(URL, json=NOVO, headers=auth)).status_code == 401  # token vazio no servidor = tudo recusado


@pytest.mark.parametrize(
    ("mudanca", "campo"),
    [
        ({"sku": "ABC123"}, "sku"),
        ({"price": "0"}, "price"),
        ({"price": "-5"}, "price"),
        ({"price": "10.999"}, "price"),
        ({"stock": -1}, "stock"),
        ({"name": ""}, "name"),
        ({"is_active": False, "stock": 2}, "body"),
        ({"intruso": 1}, "intruso"),
    ],
)
async def test_validacao_422(client, auth, mudanca, campo):
    r = await client.post(URL, json={**NOVO, **mudanca}, headers=auth)
    assert r.status_code == 422
    assert campo in {e["loc"][-1] for e in r.json()["detail"]} | {e["loc"][0] for e in r.json()["detail"]}


async def test_categoria_inexistente_e_duplicado(client, auth):
    assert (await client.post(URL, json={**NOVO, "category_slug": "nada"}, headers=auth)).status_code == 422
    assert (await client.post(URL, json=NOVO, headers=auth)).status_code == 201
    assert (await client.post(URL, json=NOVO, headers=auth)).status_code == 409


async def test_apagar(client, auth):
    assert (await client.delete(f"{URL}1/")).status_code == 401
    assert (await client.delete(f"{URL}1/", headers=auth)).status_code == 204
    assert (await client.get(f"{URL}1/")).status_code == 404


async def test_categorias_e_health(client):
    # a ORDEM de "Áudio" depende da collation do banco (SQLite compara bytes; PostgreSQL, a localidade): compare como conjunto
    assert {c["slug"] for c in (await client.get("/api/v1/categories/")).json()} == {"audio", "casa", "informatica"}
    assert (await client.get("/health/")).json() == {"status": "ok"}
