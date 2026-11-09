"""Idempotência na prática (aula 16.04), usando a API do take-home 2 em memória (arquivo temporário)."""

import os
import sys
import tempfile
from datetime import UTC, datetime, timedelta

sys.path.insert(0, "take-home-2")
os.environ["RESERVAS_DB"] = os.path.join(tempfile.mkdtemp(), "t.db")
from app.main import app
from fastapi.testclient import TestClient

with TestClient(app) as c:
    sala = c.post("/salas", json={"nome": "A", "capacidade": 4})
    print("POST /salas      ->", sala.status_code, sala.json())
    print(
        "POST /salas (2x) ->",
        c.post("/salas", json={"nome": "A", "capacidade": 4}).status_code,
        "(não é idempotente: nome único recusa)",
    )
    ini = datetime.now(UTC) + timedelta(days=1)
    corpo = {
        "sala_id": 1,
        "inicio": ini.isoformat(),
        "fim": (ini + timedelta(hours=1)).isoformat(),
        "responsavel": "ana",
    }
    r1, r2 = c.post("/reservas", json=corpo), c.post("/reservas", json=corpo)
    print("POST /reservas   ->", r1.status_code, "| repetido ->", r2.status_code, r2.json())
    print(
        "DELETE 1ª vez    ->", c.delete("/reservas/1").status_code, "| 2ª vez ->", c.delete("/reservas/1").status_code
    )
    print("GET /reservas/x  ->", c.get("/reservas?data=2026-13-45").status_code, "(entrada inválida = 422, não 500)")
