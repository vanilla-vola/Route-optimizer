#!/usr/bin/env python3
"""
Batch benchmark for IEEE-style evaluation.

Usage (from repo root, backend venv active):
  python scripts/run_benchmark_batch.py \
    --instances benchmarks/instances/*.json \
    --algorithms dcir-hybrid,pda-alns,ortools-gls,alns,td-alns-rrd \
    --time-limit 12 \
    --output results/benchmark.csv

Requires MAPBOX_ACCESS_TOKEN and DCIR_MAPBOX_PROFILES=true for traffic profiles.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.config import get_settings  # noqa: E402
from app.models.schemas import Stop  # noqa: E402
from app.services.algorithms.benchmark_runner import benchmark_algorithms  # noqa: E402


def load_instance(path: Path) -> tuple[str, list[Stop], str, bool]:
    data = json.loads(path.read_text())
    stops = [Stop(**s) for s in data["stops"]]
    return (
        data.get("id", path.stem),
        stops,
        data.get("mode", "driving-traffic"),
        data.get("round_trip", True),
    )


async def run_one(
    instance_id: str,
    stops: list[Stop],
    mode: str,
    round_trip: bool,
    algorithm_ids: list[str] | None,
    time_limit_s: int,
) -> list[dict]:
    settings = get_settings()
    rows, profile_source, best_nom, best_real = await benchmark_algorithms(
        stops,
        settings=settings,
        mode=mode,
        round_trip=round_trip,
        start_fixed=False,
        end_fixed=False,
        algorithm_ids=algorithm_ids,
        time_limit_s=time_limit_s,
    )
    out: list[dict] = []
    for row in rows:
        out.append(
            {
                "instance_id": instance_id,
                "profile_source": profile_source,
                "best_nominal_algorithm": best_nom,
                "best_realized_algorithm": best_real,
                **row,
            }
        )
    return out


async def main() -> None:
    parser = argparse.ArgumentParser(description="Batch route algorithm benchmark")
    parser.add_argument(
        "--instances",
        nargs="+",
        required=True,
        help="JSON instance files",
    )
    parser.add_argument(
        "--algorithms",
        default="drpt-alns,dcir-hybrid,pda-alns,ortools-gls,alns,td-alns-rrd,nn-2opt",
        help="Comma-separated algorithm ids",
    )
    parser.add_argument("--time-limit", type=int, default=12)
    parser.add_argument("--output", type=Path, default=Path("results/benchmark.csv"))
    args = parser.parse_args()

    algo_ids = [a.strip() for a in args.algorithms.split(",") if a.strip()]
    all_rows: list[dict] = []

    for pattern in args.instances:
        for path in sorted(Path().glob(pattern) if "*" in pattern else [Path(pattern)]):
            if not path.exists():
                continue
            instance_id, stops, mode, round_trip = load_instance(path)
            print(f"Benchmarking {instance_id} ({len(stops)} stops)...")
            rows = await run_one(
                instance_id,
                stops,
                mode,
                round_trip,
                algo_ids,
                args.time_limit,
            )
            all_rows.extend(rows)

    if not all_rows:
        print("No results.", file=sys.stderr)
        sys.exit(1)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = sorted({k for row in all_rows for k in row.keys()})
    with args.output.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"Wrote {len(all_rows)} rows to {args.output}")


if __name__ == "__main__":
    asyncio.run(main())
