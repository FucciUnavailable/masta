"""FastAPI application factory.

Serves the JSON API under ``/api`` and, when a production build of the frontend exists
(``web/dist``), the single-page app at every other path. In development the Vite dev server
serves the frontend and proxies ``/api`` here instead.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

from masta import __version__
from masta.api.routes import router


def _web_dist_dir() -> Path:
    # src/masta/api/app.py -> repo root -> web/dist
    return Path(__file__).resolve().parents[3] / "web" / "dist"


def create_app(static_dir: Path | None = None) -> FastAPI:
    app = FastAPI(title="masta", version=__version__)
    app.include_router(router)

    dist = (static_dir or _web_dist_dir()).resolve()
    if (dist / "index.html").is_file():
        _mount_frontend(app, dist)
    return app


def _mount_frontend(app: FastAPI, dist: Path) -> None:
    @app.get("/{path:path}", include_in_schema=False)
    def frontend(path: str) -> FileResponse:
        if path == "api" or path.startswith("api/"):
            raise HTTPException(status_code=404)
        candidate = (dist / path).resolve()
        if candidate.is_file() and candidate.is_relative_to(dist):
            return FileResponse(candidate)
        # Client-side routes (/goals, /check-ins, ...) all resolve to the app shell.
        return FileResponse(dist / "index.html")
