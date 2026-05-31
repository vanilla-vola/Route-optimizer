"""Compare and benchmark API routes."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from app.config import Settings, get_settings
from app.core.exceptions import MatrixError
from app.models.schemas import (
    AlgorithmInfo,
    BenchmarkRequest,
    BenchmarkResponse,
    BenchmarkResultItem,
    CompareProviderInfo,
    CompareRequest,
    CompareResponse,
    CompareResultItem,
    OrderedStop,
    Stop,
)
from app.services.algorithms.benchmark_runner import benchmark_algorithms
from app.services.algorithms.registry import list_algorithms
from app.services.compare.registry import list_providers
from app.services.solver_modes import (
    supported_modes_for_algorithm,
    supported_modes_for_provider,
)
from app.services.compare.runner import compare_routes
from app.services.geocoding import is_generic_stop_name

router = APIRouter()


def _ordered_stops(order: list[int], stops: list[Stop]) -> list[OrderedStop]:
    ordered: list[OrderedStop] = []
    for sequence, index in enumerate(order, start=1):
        stop = stops[index]
        label = stop.name.strip()
        if is_generic_stop_name(label):
            label = f"{stop.lat:.4f}, {stop.lng:.4f}"
        elif not label:
            label = f"Stop {index + 1}"
        ordered.append(
            OrderedStop(
                sequence=sequence,
                index=index,
                name=label,
                lat=stop.lat,
                lng=stop.lng,
            )
        )
    return ordered


@router.get("/algorithms", response_model=list[AlgorithmInfo])
async def list_algorithms_endpoint() -> list[AlgorithmInfo]:
    return [
        AlgorithmInfo(
            id=m.id,
            label=m.label,
            paper=m.paper,
            year=m.year,
            category=m.category,
            supported_modes=supported_modes_for_algorithm(m.id),
        )
        for m in list_algorithms()
    ]


@router.get("/compare-providers", response_model=list[CompareProviderInfo])
async def list_compare_providers_endpoint() -> list[CompareProviderInfo]:
    return [
        CompareProviderInfo(
            id=m.id,
            label=m.label,
            kind=m.kind,
            max_stops=m.max_stops,
            requires_key=m.requires_key,
            supported_modes=supported_modes_for_provider(m.id),
        )
        for m in list_providers()
    ]


@router.post("/compare-routes", response_model=CompareResponse)
async def compare_routes_endpoint(
    request: CompareRequest,
    settings: Settings = Depends(get_settings),
) -> CompareResponse:
    if len(request.stops) > settings.max_stops:
        raise HTTPException(
            status_code=400,
            detail=f"At most {settings.max_stops} stops are supported.",
        )

    try:
        results, profile_source = await compare_routes(
            request.stops,
            settings=settings,
            mode=request.mode,
            round_trip=request.round_trip,
            start_fixed=request.start_fixed,
            end_fixed=request.end_fixed,
            provider_ids=request.provider_ids,
        )
    except MatrixError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    items: list[CompareResultItem] = []
    for r in results:
        ordered: Optional[list[OrderedStop]] = None
        if r.order:
            ordered = _ordered_stops(r.order, request.stops)
        items.append(
            CompareResultItem(
                provider_id=r.provider_id,
                provider_label=r.provider_label,
                status=r.status,
                order=r.order,
                ordered_stops=ordered,
                total_duration_s=r.total_duration_s,
                total_distance_m=r.total_distance_m,
                vs_baseline_duration_pct=r.vs_baseline_duration_pct,
                message=r.message,
                manual_url=r.manual_url,
                is_baseline=r.is_baseline,
            )
        )

    return CompareResponse(
        stop_count=len(request.stops),
        mode=request.mode,
        round_trip=request.round_trip,
        profile_source=profile_source,
        results=items,
    )


@router.post("/benchmark-algorithms", response_model=BenchmarkResponse)
async def benchmark_algorithms_endpoint(
    request: BenchmarkRequest,
    settings: Settings = Depends(get_settings),
) -> BenchmarkResponse:
    if len(request.stops) > settings.max_stops:
        raise HTTPException(
            status_code=400,
            detail=f"At most {settings.max_stops} stops are supported.",
        )

    try:
        rows, profile_source = await benchmark_algorithms(
            request.stops,
            settings=settings,
            mode=request.mode,
            round_trip=request.round_trip,
            start_fixed=request.start_fixed,
            end_fixed=request.end_fixed,
            algorithm_ids=request.algorithm_ids,
            time_limit_s=request.time_limit_s,
        )
    except MatrixError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    items = [BenchmarkResultItem(**row) for row in rows]
    best_id = items[0].algorithm_id if items and items[0].status == "ok" else None

    return BenchmarkResponse(
        stop_count=len(request.stops),
        mode=request.mode,
        round_trip=request.round_trip,
        profile_source=profile_source,
        results=items,
        best_algorithm_id=best_id,
    )
