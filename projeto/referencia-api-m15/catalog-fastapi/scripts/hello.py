"""O menor FastAPI útil: tipos nas assinaturas viram validação, conversão e documentação.
Subir: uv run uvicorn scripts.hello:app --port 8830"""

from decimal import Decimal

from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(title="Hello MiniShop")


class Item(BaseModel):
    nome: str = Field(min_length=2)
    preco: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    tags: list[str] = []


@app.get("/itens/{item_id}")
async def ler(item_id: int, detalhe: bool = False) -> dict[str, object]:  # item_id vem do caminho; detalhe, da query
    return {"id": item_id, "detalhe": detalhe, "tipo_do_id": type(item_id).__name__}


@app.post("/itens", status_code=201)
async def criar(item: Item) -> Item:  # o corpo JSON é validado contra Item; o retorno também
    return item
