#!/usr/bin/env python3
"""Index all complete batch directories into PostgreSQL and Qdrant."""
import sys
import os
from pathlib import Path

# Load .env file from backend directory
backend_dir = Path(__file__).parent.parent
env_file = backend_dir / ".env"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ[key.strip()] = value.strip()

sys.path.insert(0, str(backend_dir))

from app.knowledge.indexer import index_ingestion_artifacts
from app.knowledge.embeddings import FastEmbedProvider
from app.knowledge.qdrant_store import QdrantStore

def main():
    batches_dir = backend_dir / "data" / "batches"
    if not batches_dir.exists():
        print(f"Batches directory not found: {batches_dir}")
        sys.exit(1)
    
    # Find all batch directories with merged.md and result.json
    batch_dirs = []
    for d in batches_dir.iterdir():
        if d.is_dir():
            merged_path = d / "merged.md"
            result_path = d / "result.json"
            if merged_path.exists() and result_path.exists():
                batch_dirs.append(d)
    
    print(f"Found {len(batch_dirs)} batch directories with complete artifacts")
    
    if not batch_dirs:
        print("No batch directories to index")
        sys.exit(0)
    
    # Initialize providers
    print("Initializing FastEmbed provider...")
    embedder = FastEmbedProvider()
    
    print("Initializing Qdrant store...")
    qdrant = QdrantStore()
    
    # Index each batch directory
    success_count = 0
    error_count = 0
    
    for i, batch_dir in enumerate(batch_dirs, 1):
        print(f"\n[{i}/{len(batch_dirs)}] Indexing: {batch_dir.name}")
        try:
            result = index_ingestion_artifacts(
                str(batch_dir),
                embedder=embedder,
                qdrant=qdrant,
            )
            print(f"  Success: {result}")
            success_count += 1
        except Exception as e:
            print(f"  Error: {e}")
            error_count += 1
    
    print(f"\nIndexing complete: {success_count} success, {error_count} errors")

if __name__ == "__main__":
    main()
