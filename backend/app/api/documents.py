"""Documents API (PDF v1).

Routes are thin. Real work lives in app.ingestion.* (per 03_ARCHITECTURE.md).
"""

from __future__ import annotations

import json
import os
import time
import uuid
from pathlib import Path
from threading import Lock, Thread

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

from app.ingestion.dispatcher import SUPPORTED_EXTENSIONS, run_ingest
from app.ingestion.pdf_splitter import sha256_of

router = APIRouter()


def _load_dotenv_if_present() -> None:
    """Load backend/.env into env without overwriting existing vars."""
    backend_dir = Path(__file__).resolve().parent.parent.parent
    env_path = backend_dir / ".env"
    if not env_path.exists():
        return
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if key and key not in os.environ:
            os.environ[key] = value


# In-memory indexing jobs (same pattern as reports jobs). Safe: no destructive ops.
index_jobs: dict[str, dict] = {}
index_jobs_lock = Lock()


def _scan_uploads() -> list[dict]:
    uploads = _uploads_dir()
    items: list[dict] = []
    for p in sorted(uploads.glob("*")):
        if not p.is_file():
            continue
        if p.name.startswith("tmp_"):
            continue
        items.append({
            "doc_id": p.stem,
            "filename": p.name,
            "ext": p.suffix.lower().lstrip("."),
            "path": str(p),
            "bytes": p.stat().st_size,
        })
    return items


def _scan_batches() -> list[dict]:
    batches_root = Path("data") / "batches"
    if not batches_root.exists():
        return []
    out: list[dict] = []
    for d in sorted(batches_root.iterdir()):
        if not d.is_dir():
            continue
        merged = d / "merged.md"
        result = d / "result.json"
        out.append({
            "doc_id": d.name,
            "batch_dir": str(d),
            "has_merged": merged.exists(),
            "has_result": result.exists(),
            "ready_to_index": merged.exists() and result.exists(),
        })
    return out


class IndexJobRequest(BaseModel):
    embed_batch_size: int | None = Field(
        default=None,
        ge=1,
        le=256,
        description="Embedding batch size (smaller uses less RAM). Default from EMBED_BATCH_SIZE env or 16.",
    )


@router.post("/{doc_id}/index")
def index_now(doc_id: str, body: IndexJobRequest | None = None) -> JSONResponse:
    """Sync index: store chunks+facts in PostgreSQL and vectors in Qdrant.

    Safe: upsert only. No deletes.
    """
    _load_dotenv_if_present()

    batch_dir = _batches_dir(doc_id)
    merged_path = batch_dir / "merged.md"
    result_path = batch_dir / "result.json"
    if not merged_path.exists() or not result_path.exists():
        raise HTTPException(
            status_code=409,
            detail="Missing merged.md or result.json. Run /process first and wait for merge to finish.",
        )

    from app.knowledge.indexer import index_ingestion_artifacts
    from app.knowledge.embeddings import FastEmbedProvider
    from app.knowledge.qdrant_store import QdrantStore

    embed_batch_size = (body.embed_batch_size if body else None)
    result = index_ingestion_artifacts(
        batch_dir,
        embedder=FastEmbedProvider(),
        qdrant=QdrantStore(),
        embed_batch_size=embed_batch_size,
    )
    return JSONResponse(result)


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


@router.get("/uploads")
def list_uploads() -> JSONResponse:
    """List uploaded files under data/uploads."""
    return JSONResponse({"uploads": _scan_uploads()})


@router.get("/batches")
def list_batches() -> JSONResponse:
    """List batch dirs under data/batches with readiness flags."""
    return JSONResponse({"batches": _scan_batches()})


@router.post("/index-all-job")
def start_index_all_job(body: IndexJobRequest | None = None) -> JSONResponse:
    """Index all docs that already have merged.md + result.json.

    Safe: upsert only. No deletes. Runs sequentially to reduce RAM spikes.
    """
    _load_dotenv_if_present()
    ready = [b for b in _scan_batches() if b.get("ready_to_index")]
    job_id = uuid.uuid4().hex
    with index_jobs_lock:
        index_jobs[job_id] = {
            "job_id": job_id,
            "kind": "index_all",
            "status": "queued",
            "progress": 0,
            "error": None,
            "result": None,
            "created_at": time.time(),
            "updated_at": time.time(),
            "request": (body.model_dump() if body else {}),
            "total": len(ready),
            "done": 0,
            "items": [],
        }

    def _set(**updates) -> None:
        with index_jobs_lock:
            if job_id not in index_jobs:
                return
            index_jobs[job_id].update(updates)
            index_jobs[job_id]["updated_at"] = time.time()

    def _run() -> None:
        try:
            _set(status="running", progress=0)
            from app.knowledge.indexer import index_ingestion_artifacts
            from app.knowledge.embeddings import FastEmbedProvider
            from app.knowledge.qdrant_store import QdrantStore

            embed_batch_size = (body.embed_batch_size if body else None)
            embedder = FastEmbedProvider()
            qdrant = QdrantStore()

            items_out: list[dict] = []
            for idx, item in enumerate(ready, 1):
                doc_id = str(item["doc_id"])
                try:
                    r = index_ingestion_artifacts(
                        Path(item["batch_dir"]),
                        embedder=embedder,
                        qdrant=qdrant,
                        embed_batch_size=embed_batch_size,
                    )
                    items_out.append({"doc_id": doc_id, "status": "done", "result": r})
                except Exception as exc:
                    items_out.append({"doc_id": doc_id, "status": "failed", "error": str(exc)})

                _set(
                    done=idx,
                    items=items_out,
                    progress=int((idx / max(1, len(ready))) * 100),
                )

            _set(status="done", result={"indexed": len([i for i in items_out if i["status"] == "done"]),
                                         "failed": len([i for i in items_out if i["status"] == "failed"])})
        except Exception as exc:
            _set(status="failed", error=str(exc))

    Thread(target=_run, daemon=True).start()
    return JSONResponse({"job_id": job_id, "status_url": f"/api/documents/index-job/{job_id}"})


@router.post("/{doc_id}/index-job")
def start_index_job(doc_id: str, body: IndexJobRequest | None = None) -> JSONResponse:
    """Index existing ingestion artifacts into PostgreSQL + Qdrant.

    Does NOT run ingestion. Requires data/batches/{doc_id}/merged.md and result.json.
    Async job (thread) so request does not block.
    """
    _load_dotenv_if_present()

    batch_dir = _batches_dir(doc_id)
    merged_path = batch_dir / "merged.md"
    result_path = batch_dir / "result.json"
    if not merged_path.exists() or not result_path.exists():
        raise HTTPException(
            status_code=409,
            detail="Missing merged.md or result.json. Run /process first and wait for merge to finish.",
        )

    job_id = uuid.uuid4().hex
    with index_jobs_lock:
        index_jobs[job_id] = {
            "job_id": job_id,
            "doc_id": doc_id,
            "status": "queued",
            "progress": 0,
            "error": None,
            "result": None,
            "created_at": time.time(),
            "updated_at": time.time(),
            "request": (body.model_dump() if body else {}),
        }

    def _set(**updates) -> None:
        with index_jobs_lock:
            if job_id not in index_jobs:
                return
            index_jobs[job_id].update(updates)
            index_jobs[job_id]["updated_at"] = time.time()

    def _run() -> None:
        try:
            _set(status="running", progress=0)
            from app.knowledge.indexer import index_ingestion_artifacts
            from app.knowledge.embeddings import FastEmbedProvider
            from app.knowledge.qdrant_store import QdrantStore

            embed_batch_size = (body.embed_batch_size if body else None)
            result = index_ingestion_artifacts(
                batch_dir,
                embedder=FastEmbedProvider(),
                qdrant=QdrantStore(),
                embed_batch_size=embed_batch_size,
            )
            _set(status="done", progress=100, result=result)
        except Exception as exc:
            _set(status="failed", error=str(exc))

    Thread(target=_run, daemon=True).start()
    return JSONResponse({"job_id": job_id, "status_url": f"/api/documents/index-job/{job_id}"})


@router.get("/index-job/{job_id}")
def get_index_job(job_id: str) -> JSONResponse:
    with index_jobs_lock:
        job = index_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return JSONResponse(job)
