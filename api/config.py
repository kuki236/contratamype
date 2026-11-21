"""API configuration: paths and cohort defaults."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = REPO_ROOT / "data" / "processed" / "contratamype.duckdb"
DEFAULT_YEAR = 2025

load_dotenv(REPO_ROOT / ".env")


def database_path() -> Path:
    override = os.environ.get("CONTRATAMYPE_DB")
    if override:
        return Path(override).expanduser()
    return DEFAULT_DB_PATH
