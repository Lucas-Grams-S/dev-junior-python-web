import math
from decimal import Decimal
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import ColumnElement, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import contains_eager, joinedload

from ..db import get_session
from ..models import Category, Product
from ..pagination import PageParams, link, page_params
from ..schemas import Page, ProductIn, ProductOut
from ..security import is_staff, require_staff
from ..slug import slugify

router = APIRouter(prefix="/api/v1/products", tags=["products"])

Session = Annotated[AsyncSession, Depends(get_session)]
Staff = Annotated[bool, Depends(is_staff)]

ORDERING = {"price": Product.price, "name": Product.name, "created_at": Product.created_at}


def ordenacao(ordering: str) -> tuple[Any, Any]:
    """`?ordering=-price` -> ORDER BY price DESC. Só campos da lista permitida (nada de ORDER BY livre)."""
    desc = ordering.startswith("-")
    coluna = ORDERING.get(ordering.lstrip("-"))
    if coluna is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"ordering inválido: use um de {sorted(ORDERING)} (prefixo - para decrescente).")
    return (coluna.desc() if desc else coluna.asc(), Product.id)  # id desempata: ordem estável entre páginas


@router.get("/", response_model=Page[ProductOut], summary="Lista produtos (filtros, busca, ordenação, paginação)")
async def list_products(
    request: Request,
    session: Session,
    staff: Staff,
    pg: Annotated[PageParams, Depends(page_params)],
    category: str | None = None,
    price_min: Decimal | None = None,
    price_max: Decimal | None = None,
    in_stock: bool | None = None,
    search: str | None = None,
    ordering: str = "name",
) -> Page[ProductOut]:
    where: list[ColumnElement[bool]] = []
    if not staff:  # público só vê ativos; a equipe (token) vê todos
        where.append(Product.is_active.is_(True))
    if category:
        where.append(Category.slug == category)
    if price_min is not None:
        where.append(Product.price >= price_min)
    if price_max is not None:
        where.append(Product.price <= price_max)
    if in_stock is not None:
        where.append(Product.stock > 0 if in_stock else Product.stock == 0)
    if search:
        termo = f"%{search}%"  # parâmetro vinculado (bind): sem SQL injection
        where.append(or_(Product.name.ilike(termo), Product.sku.ilike(termo), Product.description.ilike(termo)))

    total = await session.scalar(select(func.count()).select_from(Product).join(Product.category).where(*where))
    stmt = (
        select(Product)
        .join(Product.category)  # o JOIN serve ao filtro por categoria...
        .options(contains_eager(Product.category))  # ...e AS MESMAS colunas já carregam a categoria (sem 2º JOIN, sem N+1)
        .where(*where)
        .order_by(*ordenacao(ordering))
        .limit(pg.page_size)
        .offset((pg.page - 1) * pg.page_size)
    )
    rows = (await session.scalars(stmt)).unique().all()
    last = max(1, math.ceil((total or 0) / pg.page_size))
    return Page[ProductOut](
        count=total or 0,
        next=link(request, pg.page + 1, last),
        previous=link(request, pg.page - 1, last),
        results=[ProductOut.model_validate(r) for r in rows],
    )


@router.get("/{product_id}/", response_model=ProductOut)
async def get_product(product_id: int, session: Session, staff: Staff) -> Product:
    stmt = select(Product).options(joinedload(Product.category)).where(Product.id == product_id)
    if not staff:
        stmt = stmt.where(Product.is_active.is_(True))
    produto = (await session.scalars(stmt)).unique().one_or_none()
    if produto is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Não encontrado.")
    return produto


@router.post("/", response_model=ProductOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_staff)])
async def create_product(body: ProductIn, session: Session, response: Response) -> Product:
    categoria = await session.scalar(select(Category).where(Category.slug == body.category_slug))
    if categoria is None:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            [{"loc": ["body", "category_slug"], "msg": "Categoria inexistente.", "type": "value_error"}],
        )
    produto = Product(**body.model_dump(exclude={"category_slug"}), slug=slugify(body.name), category=categoria)
    session.add(produto)
    try:
        await session.commit()
    except IntegrityError:  # sku ou slug repetidos (UNIQUE no banco é a garantia final)
        await session.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Já existe um produto com este SKU ou nome.") from None
    response.headers["Location"] = f"/api/v1/products/{produto.id}/"
    return produto


@router.delete("/{product_id}/", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_staff)])
async def delete_product(product_id: int, session: Session) -> None:
    produto = await session.get(Product, product_id)
    if produto is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Não encontrado.")
    await session.delete(produto)
    await session.commit()
