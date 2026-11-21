"""Seed the deterministic fixture and serve the API for Playwright."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import uvicorn
from seed_db import default_path, seed_database

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))


def main() -> None:
    configured = (
        os.environ.get("CONTRATAMYPE_DB")
        or os.environ.get("CONTRATAMYPE_TEST_DB")
        or str(default_path())
    )
    db_path = seed_database(Path(configured))
    os.environ["CONTRATAMYPE_DB"] = str(db_path)
    port = int(os.environ.get("CONTRATAMYPE_API_PORT", "8010"))
    uvicorn.run("api.app:app", host="127.0.0.1", port=port, log_level="warning")


if __name__ == "__main__":
    main()
