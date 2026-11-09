import re
from datetime import datetime
from decimal import Decimal
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator, model_validator

SKU_RE = re.compile(r"^[A-Z]{3}-\d{3}$")


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # lê de objetos ORM (atributos), não só de dicts

    id: int
    name: str
    slug: str


class ProductIn(BaseModel):
    """Corpo do POST: a validação é declarada nos tipos e nos validadores (equivale ao ProductSerializer da escrita)."""

    model_config = ConfigDict(extra="forbid")  # campo desconhecido = erro (o DRF ignora em silêncio)

    sku: str
    name: Annotated[str, Field(min_length=1, max_length=120)]
    description: str = ""
    price: Annotated[Decimal, Field(max_digits=10, decimal_places=2)]
    stock: Annotated[int, Field(ge=0)] = 0
    is_active: bool = True
    category_slug: str

    @field_validator("sku")
    @classmethod
    def sku_formato(cls, v: str) -> str:
        v = v.strip().upper()
        if not SKU_RE.match(v):
            raise ValueError("Use o formato AAA-123 (3 letras, hífen, 3 números).")
        return v

    @field_validator("price")
    @classmethod
    def preco_positivo(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("O preço deve ser maior que zero.")
        return v

    @model_validator(mode="after")
    def regra_entre_campos(self) -> Self:
        if self.is_active is False and self.stock > 0:
            raise ValueError("Não desative um produto que ainda tem estoque.")
        return self


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sku: str
    name: str
    slug: str
    description: str
    price: Decimal
    stock: int
    is_active: bool
    category: CategoryOut
    created_at: datetime

    @computed_field  # type: ignore[prop-decorator]  # campo calculado no JSON e no OpenAPI (SerializerMethodField do DRF)
    @property
    def in_stock(self) -> bool:
        return self.stock > 0


class Page[T](BaseModel):
    """Envelope de paginação com o MESMO formato do DRF PageNumberPagination (count/next/previous/results)."""

    count: int
    next: str | None
    previous: str | None
    results: list[T]
