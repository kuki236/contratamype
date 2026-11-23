"""API configuration: database path and cohort scope."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = REPO_ROOT / "data" / "processed" / "contratamype.duckdb"
COHORT_YEARS = (2024, 2025)

load_dotenv(REPO_ROOT / ".env")


def database_path() -> Path:
    override = os.environ.get("CONTRATAMYPE_DB")
    if override:
        return Path(override).expanduser()
    return DEFAULT_DB_PATH
