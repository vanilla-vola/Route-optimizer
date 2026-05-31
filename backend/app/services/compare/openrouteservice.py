"""OpenRouteService optimization (VROOM engine, free tier)."""

from __future__ import annotations

import httpx

from app.config import Settings
from app.services.compare.base import CompareInput, CompareOutput, ProviderMeta

META = ProviderMeta(
    id="openrouteservice",
    label="OpenRouteService (VROOM)",
    kind="api",
    max_stops=50,
    requires_key="ors_api_key",
)

ORS_OPTIMIZATION_URL = "https://api.openrouteservice.org/optimization"


def _ors_profile(mode: str) -> str:
    mapping = {
        "driving": "driving-car",
        "driving-traffic": "driving-car",
        "walking": "foot-walking",
        "cycling": "cycling-regular",
    }
    return mapping.get(mode, "driving-car")


async def compare(data: CompareInput, settings: Settings) -> CompareOutput:
    if not settings.ors_api_key:
        return CompareOutput(
            provider_id=META.id,
            provider_label=META.label,
            status="skipped",
            message="ORS_API_KEY not configured — sign up free at openrouteservice.org.",
        )

    coords = data.coords
    start = coords[0]
    # Job id == stop index so ORS step["job"] maps directly into our stops list.
    job_id_to_stop = {i: i for i in range(1, len(coords))}
    jobs = [
        {"id": stop_index, "location": [coords[stop_index][0], coords[stop_index][1]]}
        for stop_index in job_id_to_stop
    ]

    vehicle: dict = {
        "id": 1,
        "profile": _ors_profile(data.mode),
        "start": [start[0], start[1]],
    }
    if data.round_trip:
        vehicle["end"] = [start[0], start[1]]
    elif data.end_fixed and len(coords) > 1:
        end = coords[-1]
        vehicle["end"] = [end[0], end[1]]

    payload = {"jobs": jobs, "vehicles": [vehicle]}

    headers = {
        "Authorization": settings.ors_api_key,
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=45.0, trust_env=False) as client:
        try:
            response = await client.post(ORS_OPTIMIZATION_URL, json=payload, headers=headers)
        except httpx.HTTPError as exc:
            return CompareOutput(
                provider_id=META.id,
                provider_label=META.label,
                status="error",
                message=f"ORS request failed: {exc}",
            )

    if response.status_code != 200:
        return CompareOutput(
            provider_id=META.id,
            provider_label=META.label,
            status="error",
            message=f"ORS error {response.status_code}: {response.text[:240]}",
        )

    body = response.json()
    routes = body.get("routes") or []
    if not routes:
        return CompareOutput(
            provider_id=META.id,
            provider_label=META.label,
            status="error",
            message="ORS returned no routes.",
        )

    route = routes[0]
    steps = route.get("steps") or []
    order: list[int] = [0]
    for step in steps:
        if step.get("type") != "job":
            continue
        job_id = int(step["job"])
        stop_index = job_id_to_stop.get(job_id)
        if stop_index is None:
            return CompareOutput(
                provider_id=META.id,
                provider_label=META.label,
                status="error",
                message=f"Unexpected ORS job id {job_id} in route response.",
            )
        order.append(stop_index)
    duration_s = int(route.get("duration", 0))
    # Distance/duration in the API response are replaced by the shared matrix in runner.
    distance_m = int(route.get("distance") or 0)

    return CompareOutput(
        provider_id=META.id,
        provider_label=META.label,
        status="ok",
        order=order,
        total_duration_s=duration_s,
        total_distance_m=distance_m,
        message="Visit order from OpenRouteService VROOM (OSM, no live traffic).",
    )
