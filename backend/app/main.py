"""FastAPI application entrypoint for the backend."""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware


def create_app() -> FastAPI:
    from .common.env import load_environment
    load_environment()
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
    frontend_origins = [
        origin.strip()
        for origin in os.getenv(
            "FRONTEND_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173",
        ).split(",")
        if origin.strip()
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=frontend_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
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

    from .api.qa import router as qa_router
    app.include_router(qa_router, prefix="/api/qa", tags=["qa"])


    return app


app = create_app()
