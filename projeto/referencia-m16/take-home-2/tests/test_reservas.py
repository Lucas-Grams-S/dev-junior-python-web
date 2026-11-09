from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta

import pytest
from app.db import iniciar
from app.main import app, caminho_db
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path):
    db = str(tmp_path / "t.db")
    iniciar(db)
    app.dependency_overrides[caminho_db] = lambda: db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def amanha(h, m=0):
    d = datetime.now(UTC) + timedelta(days=1)
    return d.replace(hour=h, minute=m, second=0, microsecond=0)


def corpo(sala, h1, h2, quem="ana", m1=0, m2=0):
    return {
        "sala_id": sala,
        "inicio": amanha(h1, m1).isoformat(),
        "fim": amanha(h2, m2).isoformat(),
        "responsavel": quem,
    }


@pytest.fixture
def sala(client):
    return client.post("/salas", json={"nome": "Azul", "capacidade": 8}).json()["id"]


def test_sala_duplicada_e_validacao(client, sala):
    assert client.post("/salas", json={"nome": "Azul", "capacidade": 4}).status_code == 409
    assert client.post("/salas", json={"nome": "X", "capacidade": 0}).status_code == 422
    assert [s["nome"] for s in client.get("/salas").json()] == ["Azul"]


def test_reservar_e_listar(client, sala):
    r = client.post("/reservas", json=corpo(sala, 10, 11))
    assert r.status_code == 201 and r.json()["responsavel"] == "ana"
    client.post("/reservas", json=corpo(sala, 8, 9, "bia"))
    dia = amanha(0).date().isoformat()
    assert [x["responsavel"] for x in client.get(f"/reservas?sala_id={sala}&data={dia}").json()] == ["bia", "ana"]


@pytest.mark.parametrize(
    ("h1", "m1", "h2", "m2", "status"),
    [
        (10, 0, 11, 0, 409),
        (9, 30, 10, 30, 409),
        (10, 30, 11, 30, 409),
        (9, 0, 12, 0, 409),
        (10, 15, 10, 45, 409),
        (9, 0, 10, 0, 201),
        (11, 0, 12, 0, 201),
    ],  # encostar nas bordas é permitido
)
def test_sobreposicao(client, sala, h1, m1, h2, m2, status):
    assert client.post("/reservas", json=corpo(sala, 10, 11)).status_code == 201
    assert client.post("/reservas", json=corpo(sala, h1, h2, m1=m1, m2=m2)).status_code == status


def test_regras_de_dominio(client, sala):
    assert client.post("/reservas", json=corpo(sala, 11, 10)).status_code == 422  # fim antes do início
    assert client.post("/reservas", json=corpo(sala, 8, 13)).status_code == 422  # 5 h
    assert client.post("/reservas", json=corpo(sala, 8, 12)).status_code == 201  # 4 h exatas
    passado = {
        "sala_id": sala,
        "inicio": (datetime.now(UTC) - timedelta(hours=2)).isoformat(),
        "fim": (datetime.now(UTC) - timedelta(hours=1)).isoformat(),
        "responsavel": "x",
    }
    assert client.post("/reservas", json=passado).status_code == 422
    sem_fuso = {**corpo(sala, 14, 15), "inicio": "2999-01-01T10:00:00", "fim": "2999-01-01T11:00:00"}
    assert client.post("/reservas", json=sem_fuso).status_code == 422  # datetime sem fuso é recusado
    assert client.post("/reservas", json=corpo(999, 14, 15)).status_code == 404


def test_fusos_diferentes_conflitam_pelo_instante(client, sala):
    from datetime import timezone

    brt = timezone(timedelta(hours=-3))
    assert client.post("/reservas", json=corpo(sala, 13, 14)).status_code == 201  # 13:00-14:00 UTC
    mesmo_instante = {
        **corpo(sala, 13, 14),
        "inicio": amanha(13).astimezone(brt).isoformat(),
        "fim": amanha(14).astimezone(brt).isoformat(),
    }
    assert mesmo_instante["inicio"].endswith("-03:00")
    assert client.post("/reservas", json=mesmo_instante).status_code == 409  # 10:00-03:00 é o MESMO instante


def test_cancelar(client, sala):
    rid = client.post("/reservas", json=corpo(sala, 10, 11)).json()["id"]
    assert client.delete(f"/reservas/{rid}").status_code == 204
    assert client.delete(f"/reservas/{rid}").status_code == 404
    assert client.post("/reservas", json=corpo(sala, 10, 11, "bia")).status_code == 201  # horário liberado


def test_concorrencia_so_uma_vence(client, sala):
    """20 threads disputam o MESMO horário: exatamente 1 recebe 201, as outras 19 recebem 409."""
    with ThreadPoolExecutor(20) as ex:
        codigos = list(
            ex.map(lambda i: client.post("/reservas", json=corpo(sala, 15, 16, f"p{i}")).status_code, range(20))
        )
    assert sorted(codigos) == [201] + [409] * 19
