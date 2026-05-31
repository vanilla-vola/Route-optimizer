"""Orchestrate multi-provider route comparison."""

from __future__ import annotations

import asyncio
from typing import Optional

from app.config import Settings
from app.models.schemas import Stop
from app.services.compare.base import CompareInput, CompareOutput
from app.services.compare.metrics import METRICS_NOTE, normalize_to_shared_matrix
from app.services.compare.registry import run_all_providers, run_provider
from app.services.coordinates import to_mapbox_coords
from app.services.matrix import build_matrix
from app.services.matrix_profiles import build_matrix_bundle


def _apply_baseline_pct(results: list[CompareOutput]) -> list[CompareOutput]:
    baseline_dur: Optional[int] = None
    for r in results:
        if r.is_baseline and r.status == "ok" and r.total_duration_s is not None:
            baseline_dur = r.total_duration_s
            break
    if baseline_dur is None or baseline_dur <= 0:
        return results

    updated: list[CompareOutput] = []
    for r in results:
        if r.status == "ok" and r.total_duration_s is not None and not r.is_baseline:
            pct = ((r.total_duration_s - baseline_dur) / baseline_dur) * 100.0
            updated.append(
                CompareOutput(
                    provider_id=r.provider_id,
                    provider_label=r.provider_label,
                    status=r.status,
                    order=r.order,
                    total_duration_s=r.total_duration_s,
                    total_distance_m=r.total_distance_m,
                    vs_baseline_duration_pct=round(pct, 1),
                    message=r.message,
                    manual_url=r.manual_url,
                    is_baseline=r.is_baseline,
                )
            )
        else:
            updated.append(r)
    return updated


async def compare_routes(
    stops: list[Stop],
    *,
    settings: Settings,
    mode: str,
    round_trip: bool,
    start_fixed: bool,
    end_fixed: bool,
    provider_ids: Optional[list[str]] = None,
) -> tuple[list[CompareOutput], str, str]:
    coords = tuple(to_mapbox_coords([{"lat": s.lat, "lng": s.lng} for s in stops]))

    distances, durations = await build_matrix(coords, settings=settings, profile=mode)
    bundle = await build_matrix_bundle(
        coords,
        settings=settings,
        profile=mode,
        base_distances=distances,
        base_durations=durations,
    )

    compare_input = CompareInput(
        stops=stops,
        coords=coords,
        mode=mode,
        round_trip=round_trip,
        start_fixed=start_fixed,
        end_fixed=end_fixed,
        duration_matrix=bundle.durations,
        distance_matrix=bundle.distances,
        profile_matrices=bundle.profile_matrices,
    )

    if provider_ids:
        results = await asyncio.gather(
            *[run_provider(pid, compare_input, settings) for pid in provider_ids]
        )
        results = list(results)
    else:
        results = await run_all_providers(compare_input, settings)

    results = normalize_to_shared_matrix(results, compare_input)
    results = _apply_baseline_pct(results)
    return results, bundle.profile_source, METRICS_NOTE
