import os
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query, Response
from pydantic import AwareDatetime, BaseModel, Field, model_validator

from .db import DB_PADRAO, conexao, iniciar

MAX_DURACAO = timedelta(hours=4)


def caminho_db() -> str:
    return os.environ.get("RESERVAS_DB", str(DB_PADRAO))


Db = Annotated[str, Depends(caminho_db)]  # dependência: os testes trocam o caminho


class SalaIn(BaseModel):
    nome: Annotated[str, Field(min_length=1, max_length=60)]
    capacidade: Annotated[int, Field(gt=0, le=500)]


class ReservaIn(BaseModel):
    sala_id: int
    inicio: AwareDatetime  # recusa datas SEM fuso: "10:00" sem fuso é ambíguo
    fim: AwareDatetime
    responsavel: Annotated[str, Field(min_length=1, max_length=80)]

    @model_validator(mode="after")
    def regras(self):
        if self.fim <= self.inicio:
            raise ValueError("fim deve ser depois do início")
        if self.fim - self.inicio > MAX_DURACAO:
            raise ValueError("duração máxima: 4 horas")
        return self


@asynccontextmanager
async def lifespan(_: FastAPI):
    iniciar(caminho_db())  # CREATE TABLE IF NOT EXISTS: idempotente
    yield


app = FastAPI(title="Reserva de salas", lifespan=lifespan)


def _iso(dt: datetime) -> str:
    return dt.astimezone(UTC).isoformat()  # guardamos tudo em UTC: comparar texto ISO UTC = comparar instantes


def _reserva(r) -> dict:
    return {
        "id": r["id"],
        "sala_id": r["sala_id"],
        "inicio": r["inicio"],
        "fim": r["fim"],
        "responsavel": r["responsavel"],
    }


@app.post("/salas", status_code=201)
def criar_sala(s: SalaIn, db: Db) -> dict:
    import sqlite3

    try:
        with conexao(db, escrita=True) as c:
            cur = c.execute("INSERT INTO salas (nome, capacidade) VALUES (?, ?)", (s.nome, s.capacidade))
            return {"id": cur.lastrowid, **s.model_dump()}
    except sqlite3.IntegrityError:
        raise HTTPException(409, "já existe uma sala com esse nome") from None


@app.get("/salas")
def listar_salas(db: Db) -> list[dict]:
    with conexao(db) as c:
        return [dict(r) for r in c.execute("SELECT id, nome, capacidade FROM salas ORDER BY nome")]


@app.post("/reservas", status_code=201)
def reservar(r: ReservaIn, db: Db) -> dict:
    if r.inicio <= datetime.now(UTC):
        raise HTTPException(422, "não é possível reservar no passado")
    ini, fim = _iso(r.inicio), _iso(r.fim)
    with conexao(db, escrita=True) as c:
        if c.execute("SELECT 1 FROM salas WHERE id = ?", (r.sala_id,)).fetchone() is None:
            raise HTTPException(404, "sala inexistente")
        # sobreposição: existente.inicio < novo.fim E existente.fim > novo.inicio (encostar não conflita)
        conflito = c.execute(
            "SELECT id FROM reservas WHERE sala_id = ? AND inicio < ? AND fim > ? LIMIT 1", (r.sala_id, fim, ini)
        ).fetchone()
        if conflito:
            raise HTTPException(409, f"conflito com a reserva {conflito['id']}")
        cur = c.execute(
            "INSERT INTO reservas (sala_id, inicio, fim, responsavel) VALUES (?, ?, ?, ?)",
            (r.sala_id, ini, fim, r.responsavel),
        )
        return {"id": cur.lastrowid, "sala_id": r.sala_id, "inicio": ini, "fim": fim, "responsavel": r.responsavel}


@app.get("/reservas")
def listar(
    db: Db, sala_id: int | None = None, data: Annotated[str | None, Query(pattern=r"^\d{4}-\d{2}-\d{2}$")] = None
) -> list[dict]:
    sql, args = "SELECT * FROM reservas WHERE 1=1", []
    if sala_id is not None:
        sql, args = sql + " AND sala_id = ?", [*args, sala_id]
    if data is not None:
        try:
            dia = datetime.fromisoformat(data).replace(tzinfo=UTC)  # dia em UTC (limitação documentada)
        except ValueError:
            raise HTTPException(422, "data inválida") from None
        sql, args = sql + " AND inicio >= ? AND inicio < ?", [*args, _iso(dia), _iso(dia + timedelta(days=1))]
    with conexao(db) as c:
        return [_reserva(x) for x in c.execute(sql + " ORDER BY inicio", args)]


@app.delete("/reservas/{rid}", status_code=204)
def cancelar(rid: int, db: Db) -> Response:
    with conexao(db, escrita=True) as c:
        if c.execute("DELETE FROM reservas WHERE id = ?", (rid,)).rowcount == 0:
            raise HTTPException(404, "reserva inexistente")
    return Response(status_code=204)
