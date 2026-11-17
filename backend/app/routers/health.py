from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.schemas import Health

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    response_model=Health,
    responses={503: {"model": Health}},
    summary="Check database connectivity and deployed version",
)
def health(db: Annotated[Session, Depends(get_db)]) -> JSONResponse:
    try:
        db.execute(select(1))
        database, status, code = "ok", "ok", 200
    except Exception:  # any DB failure means degraded, never a 500
        database, status, code = "unavailable", "degraded", 503
    body = Health(status=status, version=get_settings().version, database=database)
    return JSONResponse(body.model_dump(by_alias=True), status_code=code)
