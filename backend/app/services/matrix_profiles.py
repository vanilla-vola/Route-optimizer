"""Mapbox time-of-day profile matrices (depart_at) and scheduling helpers."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, Sequence
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import httpx

from app.config import Settings
from app.core.exceptions import MatrixError
from app.models.transport_modes import TransportMode
from app.services.matrix import MAPBOX_MATRIX_URL, UNREACHABLE_COST, _sanitize_matrix
from app.services.profiles import build_profile_matrices

DEPART_AT_PROFILES = frozenset(
    {TransportMode.DRIVING.value, TransportMode.DRIVING_TRAFFIC.value}
)
# Mapbox driving-traffic matrix allows at most 10 coordinates.
DRIVING_TRAFFIC_MATRIX_LIMIT = 10


@dataclass(frozen=True)
class MatrixBundle:
    distances: list[list[int]]
    durations: list[list[int]]
    profile_matrices: list[list[list[int]]]
    profile_source: str


def parse_depart_hours(raw: str) -> tuple[int, ...]:
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    hours = tuple(int(p) for p in parts)
    if len(hours) < 2:
        raise ValueError("dcir_depart_hours must list at least two hours, e.g. 8,13,18")
    for h in hours:
        if not 0 <= h <= 23:
            raise ValueError(f"Invalid hour in dcir_depart_hours: {h}")
    return hours


def next_departure_times(
    hours: tuple[int, ...],
    *,
    timezone: str,
) -> list[str]:
    """ISO 8601 local depart_at strings for the next occurrence of each hour."""
    tz = ZoneInfo(timezone)
    now = datetime.now(tz)
    result: list[str] = []
    for hour in hours:
        candidate = now.replace(hour=hour, minute=0, second=0, microsecond=0)
        if candidate <= now:
            candidate += timedelta(days=1)
        result.append(candidate.strftime("%Y-%m-%dT%H:%M"))
    return result


def matrix_profile_for_depart_at(profile: str, n_stops: int) -> str:
    """Pick a Mapbox profile that supports depart_at for the coordinate count."""
    if profile == TransportMode.DRIVING_TRAFFIC.value and n_stops > DRIVING_TRAFFIC_MATRIX_LIMIT:
        return TransportMode.DRIVING.value
    if profile in DEPART_AT_PROFILES:
        return profile
    return TransportMode.DRIVING.value


def supports_mapbox_depart_at(profile: str) -> bool:
    return profile in DEPART_AT_PROFILES


async def build_matrix_bundle(
    coords: Sequence[tuple[float, float]],
    *,
    settings: Settings,
    profile: str,
    base_distances: list[list[int]],
    base_durations: list[list[int]],
) -> MatrixBundle:
    """
    Return nominal distances/durations plus off-peak / nominal / peak duration matrices.

    Uses parallel Mapbox Matrix calls with depart_at when enabled; otherwise scales
    the base matrix synthetically.
    """
    if not settings.use_dcir or not settings.dcir_mapbox_profiles:
        profiles = build_profile_matrices(base_durations)
        return MatrixBundle(
            distances=base_distances,
            durations=base_durations,
            profile_matrices=profiles,
            profile_source="synthetic",
        )

    if settings.use_haversine or not settings.mapbox_access_token:
        profiles = build_profile_matrices(base_durations)
        return MatrixBundle(
            distances=base_distances,
            durations=base_durations,
            profile_matrices=profiles,
            profile_source="synthetic",
        )

    if not supports_mapbox_depart_at(profile):
        profiles = build_profile_matrices(base_durations)
        return MatrixBundle(
            distances=base_distances,
            durations=base_durations,
            profile_matrices=profiles,
            profile_source="synthetic",
        )

    try:
        hours = parse_depart_hours(settings.dcir_depart_hours)
        depart_times = next_departure_times(hours, timezone=settings.dcir_timezone)
        mapbox_profile = matrix_profile_for_depart_at(profile, len(coords))

        profile_results = await _fetch_depart_at_matrices(
            coords,
            depart_times=depart_times,
            profile=mapbox_profile,
            token=settings.mapbox_access_token,
        )

        if len(profile_results) != len(hours):
            raise MatrixError("Incomplete profile matrix set from Mapbox")

        duration_profiles = [durations for _dist, durations in profile_results]
        nominal_idx = min(len(profile_results) - 1, max(1, len(profile_results) // 2))
        nominal_distances, nominal_durations = profile_results[nominal_idx]

        return MatrixBundle(
            distances=nominal_distances,
            durations=nominal_durations,
            profile_matrices=duration_profiles,
            profile_source="mapbox-depart-at",
        )
    except (MatrixError, httpx.HTTPError, ValueError, ZoneInfoNotFoundError, OSError):
        profiles = build_profile_matrices(base_durations)
        return MatrixBundle(
            distances=base_distances,
            durations=base_durations,
            profile_matrices=profiles,
            profile_source="synthetic",
        )


async def _fetch_depart_at_matrices(
    coords: Sequence[tuple[float, float]],
    *,
    depart_times: list[str],
    profile: str,
    token: str,
) -> list[tuple[list[list[int]], list[list[int]]]]:
    async with httpx.AsyncClient(timeout=45.0, trust_env=False) as client:
        tasks = [
            _mapbox_matrix_at_departure(
                client,
                coords,
                profile=profile,
                token=token,
                depart_at=depart_at,
            )
            for depart_at in depart_times
        ]
        return list(await asyncio.gather(*tasks))


async def _mapbox_matrix_at_departure(
    client: httpx.AsyncClient,
    coords: Sequence[tuple[float, float]],
    *,
    profile: str,
    token: str,
    depart_at: str,
) -> tuple[list[list[int]], list[list[int]]]:
    coord_str = ";".join(f"{lng},{lat}" for lng, lat in coords)
    url = (
        f"{MAPBOX_MATRIX_URL}/{profile}/{coord_str}"
        f"?annotations=distance,duration"
        f"&depart_at={depart_at}"
        f"&access_token={token}"
    )

    try:
        response = await client.get(url)
    except httpx.HTTPError as exc:
        raise MatrixError(f"Could not reach Mapbox: {exc}") from exc

    if response.status_code != 200:
        raise MatrixError(f"Mapbox error {response.status_code}: {response.text}")

    data = response.json()
    raw_distances = data.get("distances")
    raw_durations = data.get("durations")
    if not raw_distances or not raw_durations:
        raise MatrixError("Invalid matrix response from Mapbox")

    return _sanitize_matrix(raw_distances, raw_durations)


async def refresh_leg_duration(
    from_coord: tuple[float, float],
    to_coord: tuple[float, float],
    *,
    settings: Settings,
    profile: str,
    depart_at: Optional[str] = None,
) -> Optional[int]:
    """
    Mapbox Directions API duration (seconds) for one leg at a specific departure.
    Returns None if unavailable.
    """
    if not settings.mapbox_access_token or settings.use_haversine:
        return None

    mapbox_profile = matrix_profile_for_depart_at(profile, 2)
    coord_str = f"{from_coord[0]},{from_coord[1]};{to_coord[0]},{to_coord[1]}"
    url = (
        f"https://api.mapbox.com/directions/v5/mapbox/{mapbox_profile}/{coord_str}"
        f"?overview=false&access_token={settings.mapbox_access_token}"
    )
    if depart_at and supports_mapbox_depart_at(mapbox_profile):
        url += f"&depart_at={depart_at}"

    async with httpx.AsyncClient(timeout=15.0, trust_env=False) as client:
        try:
            response = await client.get(url)
        except httpx.HTTPError:
            return None

    if response.status_code != 200:
        return None

    routes = response.json().get("routes")
    if not routes:
        return None
    duration = routes[0].get("duration")
    if duration is None:
        return None
    return max(1, int(duration))


def apply_leg_refresh_to_matrix(
    matrix: list[list[int]],
    from_node: int,
    to_node: int,
    duration_s: int,
) -> None:
    if (
        0 <= from_node < len(matrix)
        and 0 <= to_node < len(matrix)
        and duration_s < UNREACHABLE_COST
    ):
        matrix[from_node][to_node] = duration_s
