import re
from typing import Optional

import httpx

from app.config import Settings

GENERIC_STOP_PATTERN = re.compile(r"^stop\s*\d+$", re.IGNORECASE)
MAPBOX_GEOCODE_URL = "https://api.mapbox.com/geocoding/v5/mapbox.places"
NOMINATIM_REVERSE_URL = "https://nominatim.openstreetmap.org/reverse"


def is_generic_stop_name(name: str) -> bool:
    n = name.strip().lower()
    if not n:
        return True
    if GENERIC_STOP_PATTERN.match(n):
        return True
    return n.startswith("finding place")


async def reverse_geocode(
    lat: float,
    lng: float,
    *,
    settings: Settings,
) -> str:
    """Resolve coordinates to a short human-readable place name."""
    if settings.mapbox_access_token:
        label = await _mapbox_reverse(lat, lng, token=settings.mapbox_access_token)
        if label:
            return label

    return await _nominatim_reverse(lat, lng)


async def enrich_stop_names(stops: list, *, settings: Settings) -> list:
    """Return stops with generic names replaced by reverse-geocoded labels."""
    from app.models.schemas import Stop

    enriched: list[Stop] = []
    async with httpx.AsyncClient(timeout=15.0, trust_env=False) as client:
        for stop in stops:
            if not is_generic_stop_name(stop.name):
                enriched.append(stop)
                continue
            label = await _reverse_with_client(
                client, stop.lat, stop.lng, settings=settings,
            )
            if label:
                enriched.append(stop.model_copy(update={"name": label}))
            else:
                enriched.append(stop)
    return enriched


async def _reverse_with_client(
    client: httpx.AsyncClient,
    lat: float,
    lng: float,
    *,
    settings: Settings,
) -> Optional[str]:
    if settings.mapbox_access_token:
        label = await _mapbox_reverse(lat, lng, token=settings.mapbox_access_token, client=client)
        if label:
            return label
    return await _nominatim_reverse(lat, lng, client=client)


async def _mapbox_reverse(
    lat: float,
    lng: float,
    *,
    token: str,
    client: Optional[httpx.AsyncClient] = None,
) -> Optional[str]:
    url = (
        f"{MAPBOX_GEOCODE_URL}/{lng},{lat}.json"
        f"?access_token={token}&types=poi,address,place,locality&limit=1"
    )
    try:
        if client:
            response = await client.get(url)
        else:
            async with httpx.AsyncClient(timeout=10.0, trust_env=False) as c:
                response = await c.get(url)
        if response.status_code != 200:
            return None
        data = response.json()
        features = data.get("features") or []
        if not features:
            return None
        return _shorten_mapbox_label(features[0])
    except httpx.HTTPError:
        return None


async def _nominatim_reverse(
    lat: float,
    lng: float,
    client: Optional[httpx.AsyncClient] = None,
) -> str:
    """Free OpenStreetMap reverse geocoding (no API key)."""
    params = {
        "lat": lat,
        "lon": lng,
        "format": "json",
        "zoom": 18,
        "addressdetails": 1,
    }
    headers = {"User-Agent": "route-optimizer/1.0 (educational project)"}
    try:
        if client:
            response = await client.get(NOMINATIM_REVERSE_URL, params=params, headers=headers)
        else:
            async with httpx.AsyncClient(timeout=10.0, trust_env=False) as c:
                response = await c.get(NOMINATIM_REVERSE_URL, params=params, headers=headers)
        if response.status_code != 200:
            return _coord_fallback(lat, lng)
        data = response.json()
        return _shorten_nominatim_label(data) or _coord_fallback(lat, lng)
    except httpx.HTTPError:
        return _coord_fallback(lat, lng)


def _shorten_mapbox_label(feature: dict) -> str:
    text = feature.get("text")
    if text:
        return str(text).strip()[:80]

    place_name = feature.get("place_name") or ""
    if not place_name:
        return ""
    # First segment before comma (ASCII or Unicode).
    for sep in (",", "،"):
        if sep in place_name:
            return place_name.split(sep)[0].strip()[:80]
    return place_name.strip()[:80]


def _shorten_nominatim_label(data: dict) -> Optional[str]:
    address = data.get("address") or {}
    for key in ("amenity", "building", "road", "suburb", "neighbourhood", "city", "town", "village"):
        value = address.get(key)
        if value:
            return str(value)[:80]

    display = data.get("display_name")
    if display:
        return display.split(",")[0].strip()[:80]
    return None


def _coord_fallback(lat: float, lng: float) -> str:
    return f"{lat:.4f}, {lng:.4f}"
