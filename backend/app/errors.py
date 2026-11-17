"""Every API error returns {"code", "message"}.

FROZEN after Phase 0: add codes only via the orchestrator.
"""

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.schemas import ErrorOut

# code -> HTTP status. Routers raise ApiError(code, message); the status comes from here.
ERROR_STATUS: dict[str, int] = {
    "unauthenticated": 401,
    "invalid_credentials": 401,
    "forbidden": 403,
    "csrf_failed": 403,
    "account_disabled": 403,
    "not_found": 404,
    "conflict": 409,
    "already_answered": 409,
    "attempt_not_completed": 409,
    "nothing_to_retry": 409,
    "cannot_disable_self": 409,
    "validation_error": 422,
    "rate_limited": 429,
    "quota_exhausted": 429,
    "provider_invalid_output": 502,
    "not_implemented": 501,
    "provider_unavailable": 503,
}


class ApiError(Exception):
    def __init__(self, code: str, message: str, details: Any = None) -> None:
        if code not in ERROR_STATUS:
            raise ValueError(f"Unknown error code: {code}")
        self.code = code
        self.message = message
        self.details = details
        self.status = ERROR_STATUS[code]


def _body(code: str, message: str, details: Any = None) -> dict[str, Any]:
    body: dict[str, Any] = {"code": code, "message": message}
    if details is not None:
        body["details"] = details
    return body


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def api_error(_: Request, exc: ApiError) -> JSONResponse:
        return JSONResponse(_body(exc.code, exc.message, exc.details), status_code=exc.status)

    @app.exception_handler(RequestValidationError)
    async def validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        # Drop "input" so submitted notes/passwords never echo back or reach logs.
        details = [{"loc": e["loc"], "msg": e["msg"]} for e in exc.errors()]
        return JSONResponse(
            _body("validation_error", "Some values are invalid.", details), status_code=422
        )


def error_responses(*statuses: int) -> dict[int | str, dict[str, Any]]:
    """OpenAPI `responses=` helper so every route documents its error shapes."""
    return {s: {"model": ErrorOut} for s in statuses}
