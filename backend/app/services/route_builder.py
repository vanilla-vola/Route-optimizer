from typing import Optional

from app.models.schemas import Leg, OptimizeResponse, OrderedStop, Stop
from app.services.algorithms.metrics import realized_duration_s
from app.services.geocoding import is_generic_stop_name


def build_optimize_response(
    order: list[int],
    stops: list[Stop],
    distances: list[list[int]],
    durations: list[list[int]],
    *,
    round_trip: bool,
    mode: str,
    solver: str = "ortools-gls",
    profile_source: Optional[str] = None,
    profile_matrices: Optional[list[list[list[int]]]] = None,
) -> OptimizeResponse:
    legs, total_distance_m, total_duration_s = _summarize_legs(
        order,
        distances,
        durations,
        round_trip=round_trip,
    )
    ordered_stops = _build_ordered_stops(order, stops)
    realized = realized_duration_s(
        order, profile_matrices, round_trip=round_trip
    )

    return OptimizeResponse(
        order=order,
        ordered_stops=ordered_stops,
        total_distance_m=total_distance_m,
        total_duration_s=total_duration_s,
        legs=[Leg(**leg) for leg in legs],
        mode=mode,
        round_trip=round_trip,
        solver=solver,
        profile_source=profile_source,
        realized_duration_s=realized,
    )


def _build_ordered_stops(order: list[int], stops: list[Stop]) -> list[OrderedStop]:
    ordered: list[OrderedStop] = []
    for sequence, index in enumerate(order, start=1):
        stop = stops[index]
        label = stop.name.strip()
        if is_generic_stop_name(label):
            label = f"{stop.lat:.4f}, {stop.lng:.4f}"
        elif not label:
            label = f"Stop {index + 1}"
        ordered.append(
            OrderedStop(
                sequence=sequence,
                index=index,
                name=label,
                lat=stop.lat,
                lng=stop.lng,
            )
        )
    return ordered


def _summarize_legs(
    order: list[int],
    distances: list[list[int]],
    durations: list[list[int]],
    *,
    round_trip: bool,
) -> tuple[list[dict], int, int]:
    legs: list[dict] = []
    total_distance_m = 0
    total_duration_s = 0

    if not order:
        return legs, 0, 0

    path = list(order)
    if round_trip and len(path) > 1:
        path = path + [path[0]]

    for i in range(len(path) - 1):
        from_index = path[i]
        to_index = path[i + 1]
        distance_m = int(distances[from_index][to_index])
        duration_s = int(durations[from_index][to_index])
        total_distance_m += distance_m
        total_duration_s += duration_s
        legs.append(
            {
                "from_index": from_index,
                "to_index": to_index,
                "distance_m": distance_m,
                "duration_s": duration_s,
            }
        )

    return legs, total_distance_m, total_duration_s
