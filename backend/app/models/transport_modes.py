from enum import Enum

from pydantic import BaseModel


class TransportMode(str, Enum):
    """Mapbox Directions Matrix profiles (see Mapbox Matrix API docs)."""

    DRIVING = "driving"
    DRIVING_TRAFFIC = "driving-traffic"
    WALKING = "walking"
    CYCLING = "cycling"


# Fallback straight-line speeds when Mapbox / haversine mode is active (km/h).
HAVERSINE_SPEED_KMH: dict[str, float] = {
    TransportMode.DRIVING.value: 40.0,
    TransportMode.DRIVING_TRAFFIC.value: 32.0,
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
        description="Car routing on the road network",
    ),
    TransportModeInfo(
        id=TransportMode.DRIVING_TRAFFIC.value,
        label="Driving (traffic)",
        description="Car routing with live traffic estimates",
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
    allowed = {mode.value for mode in TransportMode}
    if cleaned not in allowed:
        allowed_list = ", ".join(sorted(allowed))
        raise ValueError(f"Unsupported mode '{value}'. Choose one of: {allowed_list}")
    return cleaned


def haversine_speed_kmh(profile: str) -> float:
    return HAVERSINE_SPEED_KMH.get(profile, HAVERSINE_SPEED_KMH[TransportMode.DRIVING.value])
