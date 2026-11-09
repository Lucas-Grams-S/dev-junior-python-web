from typing import Annotated

from fastapi import Query, Request
from pydantic import BaseModel

from .config import settings


class PageParams(BaseModel):
    page: int = 1
    page_size: int = settings.page_size


def page_params(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1)] = settings.page_size,
) -> PageParams:
    # como o DRF: o cliente pede, mas nunca passa do máximo (limita em vez de recusar)
    return PageParams(page=page, page_size=min(page_size, settings.max_page_size))


def link(request: Request, page: int, last: int) -> str | None:
    if page < 1 or page > last:
        return None
    return str(request.url.include_query_params(page=page))
