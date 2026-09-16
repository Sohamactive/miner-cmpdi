#!/usr/bin/env python3
"""Create PostgreSQL schema for MINER project."""
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

from app.extraction.postgres import create_session, create_schema
from app.extraction.models import Base

def main():
    session = create_session()
    try:
        create_schema(session)
        print("Schema created successfully")
    except Exception as e:
        print(f"Error creating schema: {e}")
        sys.exit(1)
    finally:
        session.close()

if __name__ == "__main__":
    main()
