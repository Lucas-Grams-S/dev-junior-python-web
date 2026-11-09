import sqlite3
from contextlib import contextmanager
from pathlib import Path

DB_PADRAO = Path("reservas.db")

ESQUEMA = """
CREATE TABLE IF NOT EXISTS salas (
    id INTEGER PRIMARY KEY, nome TEXT NOT NULL UNIQUE, capacidade INTEGER NOT NULL CHECK (capacidade > 0));
CREATE TABLE IF NOT EXISTS reservas (
    id INTEGER PRIMARY KEY, sala_id INTEGER NOT NULL REFERENCES salas(id),
    inicio TEXT NOT NULL, fim TEXT NOT NULL, responsavel TEXT NOT NULL, CHECK (fim > inicio));
CREATE INDEX IF NOT EXISTS reservas_sala_inicio ON reservas (sala_id, inicio);
"""


def iniciar(caminho: Path | str) -> None:
    with sqlite3.connect(caminho) as c:
        c.executescript(ESQUEMA)


@contextmanager
def conexao(caminho: Path | str, escrita: bool = False):
    """Uma conexão por requisição. Escrita = BEGIN IMMEDIATE: o 'checar sobreposição + inserir' vira UMA operação
    atômica (um escritor por vez), sem condição de corrida."""
    c = sqlite3.connect(caminho, timeout=5, isolation_level=None)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys = ON")
    try:
        c.execute("BEGIN IMMEDIATE" if escrita else "BEGIN")
        yield c
        c.execute("COMMIT")
    except BaseException:
        c.execute("ROLLBACK")
        raise
    finally:
        c.close()
