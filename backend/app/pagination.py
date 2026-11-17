from dataclasses import dataclass
from typing import Annotated, Any

from fastapi import Depends, Query
from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.schemas import Sort

PAGE_SIZE = 10


@dataclass
class PageParams:
    page: int
    q: str | None
    sort: Sort


def page_params(
    page: Annotated[int, Query(ge=1)] = 1,
    q: Annotated[str | None, Query(max_length=100)] = None,
    sort: Sort = "newest",
) -> PageParams:
    return PageParams(page=page, q=(q or "").strip() or None, sort=sort)


Paging = Annotated[PageParams, Depends(page_params)]


def paginate(db: Session, stmt: Select[Any], page: int) -> tuple[list[Any], int]:
    """Run `stmt` (already filtered + ordered) for one page; returns (rows, total)."""
    total = db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery())) or 0
    rows = db.execute(stmt.limit(PAGE_SIZE).offset((page - 1) * PAGE_SIZE)).all()
    return [r[0] if len(r) == 1 else r for r in rows], total
