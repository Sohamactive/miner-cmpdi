"""FastAPI application entrypoint for the backend."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles




def create_app() -> FastAPI:
    app = FastAPI(
        title="M.I.N.E.R. Backend",
        description=(
            "Mining Intelligence, Knowledge & Evidence Reporter. "
            "Prototype backend for PDF ingestion and evidence-grounded workflows."
        ),
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    @app.get("/", tags=["system"])
    def root() -> JSONResponse:
        return JSONResponse(
            {
                "name": "miner-backend",
                "status": "ok",
                "docs": "/docs",
            }
        )

    @app.get("/health", tags=["system"])
    def health() -> JSONResponse:
        return JSONResponse(
            {
                "status": "healthy",
            }
        )

    from .api.documents import router as documents_router
    app.include_router(documents_router, prefix="/api/documents", tags=["documents"])

    from .api.reports import router as reports_router
    app.include_router(reports_router, prefix="/api/reports", tags=["reports"])

    # Serve frontend
    frontend_dir = Path(__file__).resolve().parent.parent.parent / "frontend"
    if frontend_dir.exists():
        app.mount("/frontend", StaticFiles(directory=str(frontend_dir)), name="frontend")

    return app


app = create_app()