"""CLI: python -m contratamype run --input ..."""

from __future__ import annotations

import argparse
import json
import sys
from decimal import Decimal
from pathlib import Path

from contratamype.config import Settings
from contratamype.run import run_pipeline


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="contratamype")
    subparsers = parser.add_subparsers(dest="command", required=True)
    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--input", type=Path, required=True)
    run_parser.add_argument("--artifacts", type=Path, default=Path("artifacts/e2e"))
    run_parser.add_argument("--db", type=Path, default=Path("data/processed/contratamype.duckdb"))
    run_parser.add_argument("--year", type=int, default=2025)
    run_parser.add_argument("--cohort-year", type=int, default=2025)
    run_parser.add_argument("--mype-threshold", type=Decimal, default=Decimal("200000"))
    args = parser.parse_args(argv)

    settings = Settings(
        artifacts_dir=args.artifacts,
        db_path=args.db,
        year=args.year,
        cohort_year=args.cohort_year,
        mype_threshold=args.mype_threshold,
    )
    summary = run_pipeline(args.input, settings)
    print(json.dumps(summary, ensure_ascii=False, default=str))
    return 1 if summary["quality_gate"]["blocked"] else 0


if __name__ == "__main__":
    sys.exit(main())
