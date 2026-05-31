import math
from typing import Optional, Sequence

import httpx

from app.config import Settings
from app.core.exceptions import MatrixError
from app.models.transport_modes import haversine_speed_kmh

MAPBOX_MATRIX_URL = "https://api.mapbox.com/directions-matrix/v1/mapbox"
UNREACHABLE_COST = 999_999_999


async def build_matrix(
    coords: Sequence[tuple[float, float]],
    *,
    settings: Settings,
    profile: str,
) -> tuple[list[list[int]], list[list[int]]]:
    if settings.use_haversine or not settings.mapbox_access_token:
        return _haversine_matrix(coords, profile=profile)

    try:
        return await _mapbox_matrix(coords, profile=profile, token=settings.mapbox_access_token)
    except (MatrixError, httpx.HTTPError) as exc:
        if settings.use_haversine:
            raise
        return _haversine_matrix(coords, profile=profile, source_error=str(exc))


async def _mapbox_matrix(
    coords: Sequence[tuple[float, float]],
    *,
    profile: str,
    token: str,
) -> tuple[list[list[int]], list[list[int]]]:
    coord_str = ";".join(f"{lng},{lat}" for lng, lat in coords)
    url = (
        f"{MAPBOX_MATRIX_URL}/{profile}/{coord_str}"
        f"?annotations=distance,duration&access_token={token}"
    )

    async with httpx.AsyncClient(timeout=30.0, trust_env=False) as client:
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


def _sanitize_matrix(
    raw_distances: list[list],
    raw_durations: list[list],
) -> tuple[list[list[int]], list[list[int]]]:
    n = len(raw_distances)
    distances = [[0] * n for _ in range(n)]
    durations = [[0] * n for _ in range(n)]
    unreachable_pairs = 0

    for i in range(n):
        if len(raw_distances[i]) != n or len(raw_durations[i]) != n:
            raise MatrixError("Mapbox returned a malformed distance matrix")

        for j in range(n):
            if i == j:
                continue

            dist = raw_distances[i][j]
            dur = raw_durations[i][j]

            if dist is None or dur is None:
                unreachable_pairs += 1
                distances[i][j] = UNREACHABLE_COST
                durations[i][j] = UNREACHABLE_COST
                continue

            distances[i][j] = max(0, int(dist))
            durations[i][j] = max(0, int(dur))

    if unreachable_pairs > 0 and unreachable_pairs >= n * (n - 1):
        raise MatrixError("All stop pairs are unreachable by road according to Mapbox")

    return distances, durations


def _haversine_matrix(
    coords: Sequence[tuple[float, float]],
    *,
    profile: str = "driving",
    source_error: Optional[str] = None,
) -> tuple[list[list[int]], list[list[int]]]:
    speed_kmh = haversine_speed_kmh(profile)
    n = len(coords)
    distances = [[0] * n for _ in range(n)]
    durations = [[0] * n for _ in range(n)]

    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            meters = _haversine_meters(coords[i], coords[j])
            distances[i][j] = int(meters)
            durations[i][j] = int((meters / 1000) / speed_kmh * 3600)

    if source_error:
        pass

    return distances, durations


def _haversine_meters(a: tuple[float, float], b: tuple[float, float]) -> float:
    earth_radius_m = 6_371_000.0
    lat1, lng1 = math.radians(a[1]), math.radians(a[0])
    lat2, lng2 = math.radians(b[1]), math.radians(b[0])
    dlat = lat2 - lat1
    dlng = lng2 - lng1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng / 2) ** 2
    return 2 * earth_radius_m * math.asin(math.sqrt(h))
