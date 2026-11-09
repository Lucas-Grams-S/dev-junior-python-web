from collections.abc import Sequence
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_session
from ..models import Category
from ..schemas import CategoryOut

router = APIRouter(prefix="/api/v1/categories", tags=["categories"])


@router.get("/", response_model=list[CategoryOut])
async def list_categories(session: Annotated[AsyncSession, Depends(get_session)]) -> Sequence[Category]:
    return (await session.scalars(select(Category).order_by(Category.name))).all()
