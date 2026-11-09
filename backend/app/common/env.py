"""Load the repository-wide environment configuration."""

from __future__ import annotations

import os
from pathlib import Path


def load_environment() -> None:
    """Load the root .env without overwriting explicitly supplied variables."""
    backend_dir = Path(__file__).resolve().parents[2]
    root_env = backend_dir.parent / ".env"
    legacy_env = backend_dir / ".env"
    env_path = root_env if root_env.exists() else legacy_env
    if not env_path.exists():
        return

    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key and key not in os.environ:
            os.environ[key] = value.strip()
