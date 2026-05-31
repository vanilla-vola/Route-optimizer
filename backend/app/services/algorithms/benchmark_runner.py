"""Run all research algorithms on the same duration matrix."""

from __future__ import annotations

from typing import Optional

from app.config import Settings
from app.models.schemas import Stop
from app.services.algorithms.base import AlgorithmInput
from app.services.algorithms.metrics import realized_duration_s
from app.services.algorithms.registry import list_algorithms, run_algorithm
from app.services.coordinates import to_mapbox_coords
from app.services.matrix import build_matrix
from app.services.matrix_profiles import build_matrix_bundle


async def _run_one(
    algorithm_id: str,
    data: AlgorithmInput,
) -> tuple[str, Optional[object], Optional[str]]:
    try:
        result = await run_algorithm(algorithm_id, data)
        return algorithm_id, result, None
    except Exception as exc:
        return algorithm_id, None, str(exc)


def _apply_vs_best(
    rows: list[dict],
    *,
    duration_key: str,
    pct_key: str,
) -> None:
    best: Optional[int] = None
    for row in rows:
        if row.get("status") != "ok":
            continue
        val = row.get(duration_key)
        if val is None:
            continue
        if best is None or val < best:
            best = val

    if best is None or best <= 0:
        return

    for row in rows:
        if row.get("status") != "ok":
            continue
        val = row.get(duration_key)
        if val is None:
            continue
        row[pct_key] = round(((val - best) / best) * 100.0, 1)


def _best_id_for(rows: list[dict], duration_key: str) -> Optional[str]:
    best_id: Optional[str] = None
    best_val: Optional[int] = None
    for row in rows:
        if row.get("status") != "ok":
            continue
        val = row.get(duration_key)
        if val is None:
            continue
        if best_val is None or val < best_val:
            best_val = val
            best_id = row["algorithm_id"]
    return best_id


async def benchmark_algorithms(
    stops: list[Stop],
    *,
    settings: Settings,
    mode: str,
    round_trip: bool,
    start_fixed: bool,
    end_fixed: bool,
    algorithm_ids: Optional[list[str]] = None,
    time_limit_s: int = 12,
) -> tuple[list[dict], str, Optional[str], Optional[str]]:
    coords = tuple(to_mapbox_coords([{"lat": s.lat, "lng": s.lng} for s in stops]))
    distances, durations = await build_matrix(coords, settings=settings, profile=mode)
    bundle = await build_matrix_bundle(
        coords,
        settings=settings,
        profile=mode,
        base_distances=distances,
        base_durations=durations,
    )

    algo_input = AlgorithmInput(
        duration_matrix=bundle.durations,
        distance_matrix=bundle.distances,
        start_fixed=start_fixed,
        end_fixed=end_fixed,
        round_trip=round_trip,
        time_limit_s=time_limit_s,
        profile_matrices=bundle.profile_matrices,
        coords=coords,
        extra={"mode": mode},
    )

    ids = algorithm_ids or [m.id for m in list_algorithms()]
    rows: list[dict] = []

    # Sequential runs — fair CPU time per algorithm (no parallel OR-Tools contention).
    for aid in ids:
        _, result, error = await _run_one(aid, algo_input)
        meta = next(m for m in list_algorithms() if m.id == aid)
        if error or result is None:
            rows.append(
                {
                    "algorithm_id": meta.id,
                    "algorithm_label": meta.label,
                    "paper": meta.paper,
                    "year": meta.year,
                    "category": meta.category,
                    "status": "error",
                    "error": error or "unknown",
                }
            )
            continue

        realized = realized_duration_s(
            result.order,
            bundle.profile_matrices,
            round_trip=round_trip,
        )

        rows.append(
            {
                "algorithm_id": meta.id,
                "algorithm_label": meta.label,
                "paper": meta.paper,
                "year": meta.year,
                "category": meta.category,
                "status": "ok",
                "order": result.order,
                "total_duration_s": result.total_duration_s,
                "realized_duration_s": realized,
                "total_distance_m": result.total_distance_m,
                "notes": result.notes,
            }
        )

    _apply_vs_best(
        rows,
        duration_key="total_duration_s",
        pct_key="vs_best_duration_pct",
    )
    _apply_vs_best(
        rows,
        duration_key="realized_duration_s",
        pct_key="vs_best_realized_pct",
    )

    rows.sort(
        key=lambda r: r.get("total_duration_s")
        if r.get("total_duration_s") is not None
        else 10**12
    )

    best_nominal = _best_id_for(rows, "total_duration_s")
    best_realized = _best_id_for(rows, "realized_duration_s")
    return rows, bundle.profile_source, best_nominal, best_realized
