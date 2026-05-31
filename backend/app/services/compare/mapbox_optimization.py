"""Mapbox Optimization API v1 (Mapbox product baseline)."""

from __future__ import annotations

import httpx

from app.config import Settings
from app.models.transport_modes import TransportMode
from app.services.compare.base import CompareInput, CompareOutput, ProviderMeta

META = ProviderMeta(
    id="mapbox-optimization",
    label="Mapbox Optimization API",
    kind="api",
    max_stops=12,
    requires_key="mapbox_access_token",
)

MAPBOX_OPT_URL = "https://api.mapbox.com/optimized-trips/v1/mapbox"
MAX_STOPS = 12


def _mapbox_profile(mode: str) -> str:
    if mode == TransportMode.DRIVING_TRAFFIC.value and MAX_STOPS <= 10:
        return TransportMode.DRIVING_TRAFFIC.value
    return TransportMode.DRIVING.value


async def compare(data: CompareInput, settings: Settings) -> CompareOutput:
    n = len(data.coords)
    if n > MAX_STOPS:
        return CompareOutput(
            provider_id=META.id,
            provider_label=META.label,
            status="skipped",
            message=f"Mapbox Optimization supports at most {MAX_STOPS} stops (you have {n}).",
        )
    if not settings.mapbox_access_token:
        return CompareOutput(
            provider_id=META.id,
            provider_label=META.label,
            status="skipped",
            message="MAPBOX_ACCESS_TOKEN not configured.",
        )

    coord_str = ";".join(f"{lng},{lat}" for lng, lat in data.coords)
    profile = _mapbox_profile(data.mode)
    params = [
        f"access_token={settings.mapbox_access_token}",
        "overview=false",
    ]
    if data.round_trip:
        params.append("roundtrip=true")
    else:
        params.append("roundtrip=false")
        params.append("source=first")
        params.append("destination=last")

    url = f"{MAPBOX_OPT_URL}/{profile}/{coord_str}?{'&'.join(params)}"

    async with httpx.AsyncClient(timeout=30.0, trust_env=False) as client:
        try:
            response = await client.get(url)
        except httpx.HTTPError as exc:
            return CompareOutput(
                provider_id=META.id,
                provider_label=META.label,
                status="error",
                message=f"Mapbox request failed: {exc}",
            )

    if response.status_code != 200:
        return CompareOutput(
            provider_id=META.id,
            provider_label=META.label,
            status="error",
            message=f"Mapbox error {response.status_code}: {response.text[:200]}",
        )

    body = response.json()
    trips = body.get("trips") or []
    waypoints = body.get("waypoints") or []
    if not trips:
        return CompareOutput(
            provider_id=META.id,
            provider_label=META.label,
            status="error",
            message="Mapbox returned no optimized trip.",
        )

    trip = trips[0]
    order = [int(wp["waypoint_index"]) for wp in waypoints]
    return CompareOutput(
        provider_id=META.id,
        provider_label=META.label,
        status="ok",
        order=order,
        total_duration_s=int(trip.get("duration", 0)),
        total_distance_m=int(trip.get("distance", 0)),
        message="Mapbox native TSP optimizer on its own road/traffic model.",
    )
