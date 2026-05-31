"""Normalize compare metrics onto the shared travel matrix."""

from __future__ import annotations

from app.services.algorithms.metrics import leg_totals
from app.services.compare.base import CompareInput, CompareOutput

METRICS_NOTE = (
    "Durations and distances are summed on the shared travel matrix "
    "for each provider's visit order (fair comparison)."
)


def normalize_to_shared_matrix(
    results: list[CompareOutput],
    data: CompareInput,
) -> list[CompareOutput]:
    """Recompute totals on [data.duration_matrix] for every successful visit order."""
    normalized: list[CompareOutput] = []
    for result in results:
        if result.status != "ok" or not result.order or len(result.order) < 2:
            normalized.append(result)
            continue

        distance_m, duration_s = leg_totals(
            result.order,
            data.distance_matrix,
            data.duration_matrix,
            round_trip=data.round_trip,
        )
        normalized.append(
            CompareOutput(
                provider_id=result.provider_id,
                provider_label=result.provider_label,
                status=result.status,
                order=result.order,
                total_duration_s=duration_s,
                total_distance_m=distance_m,
                vs_baseline_duration_pct=result.vs_baseline_duration_pct,
                message=result.message,
                manual_url=result.manual_url,
                is_baseline=result.is_baseline,
            )
        )
    return normalized
