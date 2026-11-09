#!/usr/bin/env python3
"""Create PostgreSQL schema for MINER project."""
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.common.env import load_environment
from app.extraction.postgres import create_session, create_schema
from app.extraction.models import Base

def main():
    load_environment()
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
