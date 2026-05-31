"""Supported transport modes per solver (compare provider or research algorithm)."""

from __future__ import annotations

from app.models.transport_modes import TransportMode

ALL_MODES = [
    TransportMode.DRIVING.value,
    TransportMode.WALKING.value,
    TransportMode.CYCLING.value,
]

DRIVING_ONLY = [TransportMode.DRIVING.value]

# Manual map links do not accept a transport profile in the API.
_MANUAL_PROVIDER_MODES: dict[str, list[str]] = {
    "google-maps-manual": DRIVING_ONLY,
    "apple-maps-manual": DRIVING_ONLY,
}


def supported_modes_for_provider(provider_id: str) -> list[str]:
    return list(_MANUAL_PROVIDER_MODES.get(provider_id, ALL_MODES))


def supported_modes_for_algorithm(algorithm_id: str) -> list[str]:
    # Research solvers run on the same Mapbox/haversine matrix for any profile.
    return list(ALL_MODES)
