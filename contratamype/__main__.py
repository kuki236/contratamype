"""CLI: pipeline runs and alert digests."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

from contratamype.alerts import build_digest
from contratamype.config import DEFAULT_COHORT_YEARS, Settings
from contratamype.run import run_pipeline


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="contratamype")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run")
    run_parser.add_argument(
        "--input",
        type=Path,
        action="append",
        required=True,
        help="OCDS snapshot; repeat for multiple years (processed in year order)",
    )
    run_parser.add_argument("--artifacts", type=Path, default=Path("artifacts/e2e"))
    run_parser.add_argument("--db", type=Path, default=Path("data/processed/contratamype.duckdb"))
    run_parser.add_argument("--year", type=int, default=2025)
    run_parser.add_argument(
        "--cohort-year",
        type=int,
        action="append",
        default=None,
        help="cohort year; repeat for several (default: 2024 and 2025)",
    )
    run_parser.add_argument("--mype-threshold", type=Decimal, default=Decimal("200000"))

    digest_parser = subparsers.add_parser("digest")
    digest_parser.add_argument(
        "--db", type=Path, default=Path("data/processed/contratamype.duckdb")
    )
    digest_parser.add_argument("--artifacts", type=Path, default=Path("artifacts"))
    digest_parser.add_argument("--out", type=Path, default=Path("artifacts/alerts"))
    digest_parser.add_argument("--state", type=Path, default=Path("artifacts/alerts/state.json"))
    digest_parser.add_argument("--since", type=date.fromisoformat, required=True)
    digest_parser.add_argument("--until", type=date.fromisoformat, default=None)
    digest_parser.add_argument(
        "--cohort-year",
        type=int,
        action="append",
        default=None,
        help="cohort year; repeat for several (default: 2024 and 2025)",
    )

    args = parser.parse_args(argv)

    if args.command == "digest":
        summary = build_digest(
            db_path=args.db,
            artifacts_dir=args.artifacts,
            out_dir=args.out,
            state_path=args.state,
            since=args.since,
            until=args.until,
            cohort_years=tuple(args.cohort_year) if args.cohort_year else DEFAULT_COHORT_YEARS,
        )
        print(json.dumps(summary, ensure_ascii=False, default=str))
        return 0

    settings = Settings(
        artifacts_dir=args.artifacts,
        db_path=args.db,
        year=args.year,
        cohort_years=tuple(args.cohort_year) if args.cohort_year else DEFAULT_COHORT_YEARS,
        mype_threshold=args.mype_threshold,
    )
    summary = run_pipeline(args.input, settings)
    print(json.dumps(summary, ensure_ascii=False, default=str))
    return 1 if summary["quality_gate"]["blocked"] else 0


if __name__ == "__main__":
    sys.exit(main())
