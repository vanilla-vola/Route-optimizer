"""Google Maps manual deep link (no free optimization API for consumer Maps)."""

from __future__ import annotations

from urllib.parse import quote

from app.config import Settings
from app.services.compare.base import CompareInput, CompareOutput, ProviderMeta

META = ProviderMeta(
    id="google-maps-manual",
    label="Google Maps (manual check)",
    kind="manual",
)


def build_google_maps_url(coords: tuple[tuple[float, float], ...], *, round_trip: bool) -> str:
    """Build a Google Maps directions URL for the same stops."""
    if not coords:
        return "https://www.google.com/maps"

    parts = [f"{lat},{lng}" for lng, lat in coords]
    if round_trip and len(parts) > 1:
        parts.append(parts[0])

    path = "/".join(quote(p, safe=",") for p in parts)
    return f"https://www.google.com/maps/dir/{path}"


async def compare(data: CompareInput, settings: Settings) -> CompareOutput:
    url = build_google_maps_url(data.coords, round_trip=data.round_trip)
    return CompareOutput(
        provider_id=META.id,
        provider_label=META.label,
        status="manual",
        manual_url=url,
        message="Open Google Maps to compare ETA and visit order manually (no free public API).",
    )
