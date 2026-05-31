import re
from typing import Optional
from urllib.parse import quote

import httpx

from app.config import Settings
from app.models.schemas import PlaceSuggestion

GENERIC_STOP_PATTERN = re.compile(r"^stop\s*\d+$", re.IGNORECASE)
MAPBOX_GEOCODE_URL = "https://api.mapbox.com/geocoding/v5/mapbox.places"
NOMINATIM_REVERSE_URL = "https://nominatim.openstreetmap.org/reverse"
NOMINATIM_SEARCH_URL = "https://nominatim.openstreetmap.org/search"
NOMINATIM_HEADERS = {"User-Agent": "route-optimizer/1.0 (educational project)"}


def is_generic_stop_name(name: str) -> bool:
    n = name.strip().lower()
    if not n:
        return True
    if GENERIC_STOP_PATTERN.match(n):
        return True
    return n.startswith("finding place")


async def search_places(
    query: str,
    *,
    settings: Settings,
    limit: int = 6,
) -> list[PlaceSuggestion]:
    """Forward geocode a text query into place suggestions."""
    q = query.strip()
    if len(q) < 2:
        return []

    capped = max(1, min(limit, 10))
    if settings.mapbox_access_token:
        results = await _mapbox_search(q, token=settings.mapbox_access_token, limit=capped)
        if results:
            return results

    return await _nominatim_search(q, limit=capped)


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
    try:
        if client:
            response = await client.get(
                NOMINATIM_REVERSE_URL, params=params, headers=NOMINATIM_HEADERS,
            )
        else:
            async with httpx.AsyncClient(timeout=10.0, trust_env=False) as c:
                response = await c.get(
                    NOMINATIM_REVERSE_URL, params=params, headers=NOMINATIM_HEADERS,
                )
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


async def _mapbox_search(
    query: str,
    *,
    token: str,
    limit: int,
) -> list[PlaceSuggestion]:
    url = (
        f"{MAPBOX_GEOCODE_URL}/{quote(query, safe='')}.json"
        f"?access_token={token}&limit={limit}"
        "&types=poi,address,place,locality,neighborhood"
    )
    try:
        async with httpx.AsyncClient(timeout=10.0, trust_env=False) as client:
            response = await client.get(url)
        if response.status_code != 200:
            return []
        features = response.json().get("features") or []
        suggestions: list[PlaceSuggestion] = []
        for feature in features:
            center = feature.get("center")
            if not center or len(center) < 2:
                continue
            lng, lat = float(center[0]), float(center[1])
            name = _shorten_mapbox_label(feature)
            if not name:
                continue
            subtitle = _mapbox_subtitle(feature)
            suggestions.append(
                PlaceSuggestion(name=name, lat=lat, lng=lng, subtitle=subtitle),
            )
        return suggestions
    except httpx.HTTPError:
        return []


async def _nominatim_search(query: str, *, limit: int) -> list[PlaceSuggestion]:
    params = {
        "q": query,
        "format": "json",
        "limit": limit,
        "addressdetails": 0,
    }
    try:
        async with httpx.AsyncClient(timeout=10.0, trust_env=False) as client:
            response = await client.get(
                NOMINATIM_SEARCH_URL, params=params, headers=NOMINATIM_HEADERS,
            )
        if response.status_code != 200:
            return []
        rows = response.json()
        if not isinstance(rows, list):
            return []
        suggestions: list[PlaceSuggestion] = []
        for row in rows:
            try:
                lat = float(row["lat"])
                lng = float(row["lon"])
            except (KeyError, TypeError, ValueError):
                continue
            display = str(row.get("display_name") or "").strip()
            if not display:
                continue
            name, subtitle = _split_display_name(display)
            suggestions.append(
                PlaceSuggestion(name=name, lat=lat, lng=lng, subtitle=subtitle),
            )
        return suggestions
    except httpx.HTTPError:
        return []


def _mapbox_subtitle(feature: dict) -> str:
    place_name = str(feature.get("place_name") or "").strip()
    title = _shorten_mapbox_label(feature)
    if not place_name or not title:
        return ""
    if place_name.startswith(title):
        rest = place_name[len(title) :].lstrip(" ,")
        return rest[:200]
    return place_name[:200]


def _split_display_name(display: str) -> tuple[str, str]:
    parts = [p.strip() for p in display.split(",") if p.strip()]
    if not parts:
        return display[:80], ""
    name = parts[0][:80]
    subtitle = ", ".join(parts[1:])[:200] if len(parts) > 1 else ""
    return name, subtitle
