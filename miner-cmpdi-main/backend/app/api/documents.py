"""Documents API (PDF v1).

Routes are thin. Real work lives in app.ingestion.* (per 03_ARCHITECTURE.md).
"""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse

from app.ingestion.dispatcher import SUPPORTED_EXTENSIONS, run_ingest
from app.ingestion.pdf_splitter import sha256_of

router = APIRouter()


def _uploads_dir() -> Path:
    d = Path("data") / "uploads"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _batches_dir(doc_id: str) -> Path:
    d = Path("data") / "batches" / doc_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def _find_stored_file(doc_id: str) -> Path | None:
    uploads = _uploads_dir()
    # Check exact sha with any extension
    for p in uploads.glob(f"{doc_id}.*"):
        if p.is_file() and not p.name.startswith("tmp_"):
            return p
    return None


def _result_json_path(doc_id: str) -> Path:
    return _batches_dir(doc_id) / "result.json"


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)) -> JSONResponse:
    """Upload a document (PDF, Spreadsheet, or Image) and store under data/uploads/{sha256}.{ext}."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename")

    ext = Path(file.filename).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{ext}'. Supported formats: {sorted(SUPPORTED_EXTENSIONS)}",
        )

    uploads = _uploads_dir()
    tmp_path = uploads / f"tmp_{file.filename}"

    # Save upload to temp first
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")

    tmp_path.write_bytes(data)

    # Compute sha256 = doc_id
    doc_id = sha256_of(tmp_path)

    final_path = uploads / f"{doc_id}{ext}"
    if not final_path.exists():
        tmp_path.replace(final_path)
    else:
        # already uploaded before (dedupe)
        tmp_path.unlink(missing_ok=True)

    return JSONResponse(
        {
            "doc_id": doc_id,
            "filename": file.filename,
            "format": ext.removeprefix("."),
            "stored_path": str(final_path),
        }
    )


@router.post("/{doc_id}/process")
def process_document(
    doc_id: str,
    workers: int | None = None,
    preset: str | None = None,
    device: str = "auto",
    auto_detect: bool = True,
) -> JSONResponse:
    """Run ingestion on the uploaded document."""
    file_path = _find_stored_file(doc_id)
    if not file_path or not file_path.exists():
        raise HTTPException(
            status_code=404, detail=f"Unknown doc_id or missing upload: {doc_id}"
        )

    try:
        result = run_ingest(
            file_path,
            preset=preset,
            device=device,
            verbose=False,
            resume=True,
            max_workers=workers,
            auto_detect=auto_detect,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {exc}") from exc

    return JSONResponse(result)


@router.get("/{doc_id}/result")
def get_result(doc_id: str) -> JSONResponse:
    """Return the last saved result.json for this doc_id."""
    p = _result_json_path(doc_id)
    if not p.exists():
        raise HTTPException(
            status_code=404, detail="No result yet. Run /process first."
        )
    return JSONResponse(json.loads(p.read_text(encoding="utf-8")))


@router.get("/{doc_id}/merged.md")
def download_merged_markdown(doc_id: str) -> FileResponse:
    """Download merged markdown output."""
    p = _batches_dir(doc_id) / "merged.md"
    if not p.exists():
        raise HTTPException(
            status_code=404, detail="merged.md not found. Run /process first."
        )
    return FileResponse(
        path=str(p), filename=f"{doc_id}.merged.md", media_type="text/markdown"
    )
