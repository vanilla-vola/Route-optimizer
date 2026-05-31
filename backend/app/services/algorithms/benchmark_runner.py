"""Run all research algorithms on the same duration matrix."""

from __future__ import annotations

import asyncio
from typing import Optional

from app.config import Settings
from app.models.schemas import Stop
from app.services.algorithms.base import AlgorithmInput
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


async def benchmark_algorithms(
    stops: list[Stop],
    *,
    settings: Settings,
    mode: str,
    round_trip: bool,
    start_fixed: bool,
    end_fixed: bool,
    algorithm_ids: Optional[list[str]] = None,
    time_limit_s: int = 8,
) -> tuple[list[dict], str]:
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
    raw = await asyncio.gather(*[_run_one(aid, algo_input) for aid in ids])

    rows: list[dict] = []
    best_id: Optional[str] = None
    best_dur: Optional[int] = None

    for aid, result, error in raw:
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

        dur = result.total_duration_s
        if best_dur is None or dur < best_dur:
            best_dur = dur
            best_id = meta.id

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
                "total_distance_m": result.total_distance_m,
                "notes": result.notes,
            }
        )

    if best_dur is not None and best_dur > 0:
        for row in rows:
            if row.get("status") == "ok" and row.get("total_duration_s") is not None:
                pct = ((row["total_duration_s"] - best_dur) / best_dur) * 100.0
                row["vs_best_duration_pct"] = round(pct, 1)

    rows.sort(
        key=lambda r: r.get("total_duration_s") if r.get("total_duration_s") is not None else 10**12
    )
    return rows, bundle.profile_source
