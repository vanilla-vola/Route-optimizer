"""Tests for fair compare metric normalization."""

from app.models.schemas import Stop
from app.services.compare.base import CompareInput, CompareOutput
from app.services.compare.metrics import METRICS_NOTE, normalize_to_shared_matrix


def _matrix() -> tuple[list[list[int]], list[list[int]]]:
    distances = [
        [0, 1000, 2000],
        [1000, 0, 1500],
        [2000, 1500, 0],
    ]
    durations = [
        [0, 600, 1200],
        [600, 0, 900],
        [1200, 900, 0],
    ]
    return distances, durations


def _input() -> CompareInput:
    distances, durations = _matrix()
    return CompareInput(
        stops=[
            Stop(lat=19.0, lng=72.0, name="A"),
            Stop(lat=19.1, lng=72.1, name="B"),
            Stop(lat=19.2, lng=72.2, name="C"),
        ],
        coords=((72.0, 19.0), (72.1, 19.1), (72.2, 19.2)),
        mode="driving-traffic",
        round_trip=True,
        start_fixed=False,
        end_fixed=False,
        duration_matrix=durations,
        distance_matrix=distances,
    )


def test_normalize_replaces_mismatched_provider_duration():
    data = _input()
    order = [0, 2, 1]
    results = [
        CompareOutput(
            provider_id="openrouteservice",
            provider_label="ORS",
            status="ok",
            order=order,
            total_duration_s=7200,
            total_distance_m=103_370,
            message="native ORS",
        )
    ]

    normalized = normalize_to_shared_matrix(results, data)

    assert len(normalized) == 1
    row = normalized[0]
    assert row.total_duration_s == 1200 + 900 + 600
    assert row.total_distance_m == 2000 + 1500 + 1000
    assert row.message == "native ORS"


def test_normalize_skips_non_ok_results():
    data = _input()
    results = [
        CompareOutput(
            provider_id="openrouteservice",
            provider_label="ORS",
            status="error",
            message="failed",
        )
    ]
    assert normalize_to_shared_matrix(results, data) == results


def test_metrics_note_present():
    assert "shared travel matrix" in METRICS_NOTE
