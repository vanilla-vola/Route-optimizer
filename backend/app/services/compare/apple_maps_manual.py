"""Apple Maps manual deep link."""

from __future__ import annotations

from urllib.parse import quote

from app.config import Settings
from app.services.compare.base import CompareInput, CompareOutput, ProviderMeta

META = ProviderMeta(
    id="apple-maps-manual",
    label="Apple Maps (manual check)",
    kind="manual",
)


def build_apple_maps_url(coords: tuple[tuple[float, float], ...]) -> str:
    if len(coords) < 2:
        return "https://maps.apple.com/"
    dest_lng, dest_lat = coords[-1]
    saddr_lng, saddr_lat = coords[0]
    daddr = quote(f"{dest_lat},{dest_lng}", safe=",")
    saddr = quote(f"{saddr_lat},{saddr_lng}", safe=",")
    return f"https://maps.apple.com/?saddr={saddr}&daddr={daddr}"


async def compare(data: CompareInput, settings: Settings) -> CompareOutput:
    url = build_apple_maps_url(data.coords)
    return CompareOutput(
        provider_id=META.id,
        provider_label=META.label,
        status="manual",
        manual_url=url,
        message="Open Apple Maps for manual comparison (multi-stop API not publicly available).",
    )
