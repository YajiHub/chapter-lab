"""One JSON log line per request. Never logs query strings, bodies, headers, or cookies."""

import json
import logging
import re
import sys
import time
import uuid
from collections.abc import Awaitable, Callable, MutableMapping
from typing import Any

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

logger = logging.getLogger("chapterlab.request")
if not logger.handlers:
    _handler = logging.StreamHandler(sys.stdout)
    _handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(_handler)
    logger.setLevel(logging.INFO)

_VALID_ID = re.compile(r"[A-Za-z0-9-]{1,64}")
REQUEST_ID_HEADER = "X-Request-ID"


def _route_template(scope: MutableMapping[str, Any]) -> str:
    # FastAPI >=0.16x includes routers lazily: scope["route"].path lacks the include prefix,
    # the full template lives on the (private) effective route context.
    ctx = (scope.get("fastapi") or {}).get("effective_route_context")
    route = scope.get("route")
    return getattr(ctx, "path_format", None) or getattr(route, "path", None) or "unmatched"


def install_request_logging(app: FastAPI) -> None:
    @app.middleware("http")
    async def request_logging(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        incoming = request.headers.get(REQUEST_ID_HEADER, "")
        request_id = incoming if _VALID_ID.fullmatch(incoming) else uuid.uuid4().hex
        start = time.perf_counter()
        error = None
        try:
            response = await call_next(request)
        except Exception as exc:
            # Type only: exception messages can carry notes or provider output.
            error = type(exc).__name__
            response = JSONResponse(
                {"code": "internal_error", "message": "Something went wrong."}, status_code=500
            )
        line = {
            "request_id": request_id,
            "method": request.method,
            "route": _route_template(request.scope),
            "status": response.status_code,
            "duration_ms": round((time.perf_counter() - start) * 1000, 2),
            "user_id": getattr(request.state, "user_id", None),
        }
        if error:
            line["error"] = error
        (logger.error if error else logger.info)(json.dumps(line))
        response.headers[REQUEST_ID_HEADER] = request_id
        return response
