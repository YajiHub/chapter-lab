from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.errors import ApiError, install_error_handlers
from app.logging import install_request_logging
from app.routers import admin, attempts, auth, health, lessons, packs, reports

# Built React app; present in the Docker image, absent in local backend-only dev.
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


def create_app() -> FastAPI:
    app = FastAPI(
        title="ChapterLab API",
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url=None,
        openapi_url="/api/openapi.json",
    )
    install_error_handlers(app)
    install_request_logging(app)

    app.include_router(health.router, prefix="/api")
    for r in (auth, lessons, packs, attempts, reports, admin):
        app.include_router(r.router, prefix="/api/v1")

    if STATIC_DIR.is_dir():
        app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")

        @app.get("/{path:path}", include_in_schema=False)
        def spa(path: str) -> FileResponse:
            # Unknown /api paths must 404 as JSON, not return the SPA shell.
            if path.startswith("api/"):
                raise ApiError("not_found", "No such endpoint.")
            file = (STATIC_DIR / path).resolve()
            if path and file.is_file() and file.is_relative_to(STATIC_DIR):
                return FileResponse(file)
            return FileResponse(STATIC_DIR / "index.html")

    return app


app = create_app()
