from enum import Enum

from pydantic import BaseModel


class TransportMode(str, Enum):
    """Mapbox Directions Matrix profiles."""

    DRIVING = "driving-traffic"
    WALKING = "walking"
    CYCLING = "cycling"


# Legacy alias accepted from older clients.
_MODE_ALIASES = {
    "driving": TransportMode.DRIVING.value,
}

HAVERSINE_SPEED_KMH: dict[str, float] = {
    TransportMode.DRIVING.value: 35.0,
    TransportMode.WALKING.value: 5.0,
    TransportMode.CYCLING.value: 15.0,
}


class TransportModeInfo(BaseModel):
    id: str
    label: str
    description: str


TRANSPORT_MODE_CATALOG: list[TransportModeInfo] = [
    TransportModeInfo(
        id=TransportMode.DRIVING.value,
        label="Driving",
        description="Car routing with live traffic-aware travel times",
    ),
    TransportModeInfo(
        id=TransportMode.WALKING.value,
        label="Walking",
        description="Pedestrian paths and walkways",
    ),
    TransportModeInfo(
        id=TransportMode.CYCLING.value,
        label="Cycling",
        description="Bike-friendly roads and paths",
    ),
]


def normalize_mode(value: str) -> str:
    cleaned = value.strip().lower()
    cleaned = _MODE_ALIASES.get(cleaned, cleaned)
    allowed = {mode.value for mode in TransportMode}
    if cleaned not in allowed:
        allowed_list = ", ".join(sorted(allowed))
        raise ValueError(f"Unsupported mode '{value}'. Choose one of: {allowed_list}")
    return cleaned


def haversine_speed_kmh(profile: str) -> float:
    try:
        normalized = normalize_mode(profile)
    except ValueError:
        normalized = TransportMode.DRIVING.value
    return HAVERSINE_SPEED_KMH.get(normalized, HAVERSINE_SPEED_KMH[TransportMode.DRIVING.value])
