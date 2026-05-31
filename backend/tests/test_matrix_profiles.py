"""Tests for Mapbox profile scheduling helpers."""

from datetime import datetime
from zoneinfo import ZoneInfo

from app.services.matrix_profiles import parse_depart_hours, next_departure_times
from app.services.profiles import build_profile_matrices


def test_parse_depart_hours():
    assert parse_depart_hours("8,13,18") == (8, 13, 18)


def test_next_departure_times_format():
    times = next_departure_times((8, 13, 18), timezone="Asia/Kolkata")
    assert len(times) == 3
    for t in times:
        assert "T" in t
        datetime.strptime(t, "%Y-%m-%dT%H:%M").replace(tzinfo=ZoneInfo("Asia/Kolkata"))


def test_synthetic_profiles_three_layers():
    nominal = [[0, 100], [110, 0]]
    profiles = build_profile_matrices(nominal)
    assert len(profiles) == 3
    assert profiles[1][0][1] == 100
    assert profiles[0][0][1] < 100
    assert profiles[2][0][1] > 100
