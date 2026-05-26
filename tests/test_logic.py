"""Unit tests for src/logic.py module."""

import pytest

from src.logic import (
    timestamp_str_to_seconds,
    seconds_to_timestamp_str,
    is_timed_out,
    format_duration,
    haversine,
    get_nearby_geohashes,
)


def test_timestamp_str_to_seconds_valid() -> None:
    # Test with a valid ISO-8601 timestamp string
    seconds = timestamp_str_to_seconds("2024-05-19T10:30:00Z")
    assert isinstance(seconds, float)
    assert seconds > 0


def test_seconds_to_timestamp_str_roundtrip() -> None:
    # Test that converting seconds to a timestamp string and back yields the original seconds
    original_seconds = 1716114600.0
    timestamp_str = seconds_to_timestamp_str(original_seconds)
    assert timestamp_str == "2024-05-19T10:30:00Z"
    assert timestamp_str_to_seconds(timestamp_str) == original_seconds


def test_timestamp_str_to_seconds_invalid_format() -> None:
    # Test with an invalid ISO-8601 timestamp string
    with pytest.raises(ValueError, match="Invalid ISO-8601"):
        timestamp_str_to_seconds("2024-05-19_10-30-00") # Invalid format, instead of "2024-05-19T10:30:00Z"


# ==================== Timeout Tests ====================


def test_is_timed_out_within_window() -> None:
    # Test that a request is not timed out if current time is within the timeout window
    request_time = 1000.0
    current_time = 1200.0  # 200 seconds later and not 300 seconds later
    assert not is_timed_out(request_time, current_time)


def test_is_not_timed_out_at_exact_default_timeout() -> None:
    # Test that a request is not timed out if current time is exactly at the default timeout threshold
    request_time = 1000.0
    current_time = 1300.0  # exactly 300 seconds later
    assert not is_timed_out(request_time, current_time)


def test_is_timed_out_exceeds_default_timeout() -> None:
    # Test that a request is timed out if current time exceeds the default timeout threshold
    request_time = 1000.0
    current_time = 1400.0  # 400 seconds later (exceeds 300s default)
    assert is_timed_out(request_time, current_time)


def test_is_timed_out_custom_timeout() -> None:
    # Test that a request is timed out based on a custom timeout value
    request_time = 1000.0
    current_time = 1150.0  # 150 seconds later
    assert not is_timed_out(request_time, current_time, timeout_seconds=200.0)
    assert is_timed_out(request_time, current_time, timeout_seconds=100.0)


# ==================== Duration Formatting Tests ====================


def test_format_duration_seconds_only() -> None:
    # Test formatting a duration that is less than one minute
    result = format_duration(45.0)
    assert result == "00:00:45"


def test_format_duration_minutes_and_seconds() -> None:
    # Test formatting a duration that includes minutes and seconds
    result = format_duration(125.0)  # 2 min 5 sec
    assert result == "00:02:05"


def test_format_duration_hours_and_minutes_and_seconds() -> None:
    # Test formatting a duration that includes hours, minutes, and seconds
    result = format_duration(3665.0)  # 1 hour 1 min 5 sec
    assert result == "01:01:05"


def test_format_duration_zero() -> None:
    # Test formatting a duration of zero seconds
    result = format_duration(0.0)
    assert result == "00:00:00"


# ==================== Haversine Tests ====================


def test_haversine_same_point_is_zero() -> None:
    # Test that the distance between the same point is zero
    distance = haversine(51.5074, -0.1278, 51.5074, -0.1278)
    assert pytest.approx(distance, abs=1e-9) == 0.0


def test_haversine_equatorial_degree() -> None:
    # Test that the distance for one degree of longitude at the equator is approximately 111.195 km
    distance = haversine(0.0, 0.0, 0.0, 1.0)
    assert pytest.approx(distance, rel=1e-3) == 111.195


def test_haversine_meridian_distance() -> None:
    # Test that the distance for one degree of latitude is approximately 111.195 km
    distance = haversine(0.0, 0.0, 1.0, 0.0)
    assert pytest.approx(distance, rel=1e-3) == 111.195


def test_haversine_london_to_paris() -> None:
    # Test the distance between London and Paris is approximately 343 km
    # London: 51.5074, -0.1278
    # Paris: 48.8566, 2.3522
    distance = haversine(51.5074, -0.1278, 48.8566, 2.3522)
    assert 340 < distance < 350  # Approximate distance


# ==================== Geohash Neighborhood Tests ====================


def test_get_nearby_geohashes_valid() -> None:
    # Test that the function returns 9 geohashes including the center geohash
    geohash = "u33db"
    neighbors = get_nearby_geohashes(geohash)
    assert len(neighbors) == 9
    assert geohash in neighbors


def test_get_nearby_geohashes_includes_center() -> None:
    # Test that the center geohash is included in the list of nearby geohashes
    geohash = "ez" 
    neighbors = get_nearby_geohashes(geohash)
    assert geohash == neighbors[0]


def test_get_nearby_geohashes_invalid_empty() -> None:
    # Test that the function raises a ValueError when given an empty string
    with pytest.raises(ValueError, match="non-empty string"):
        get_nearby_geohashes("")


def test_get_nearby_geohashes_invalid_none() -> None:
    # Test that the function raises a ValueError when given None
    with pytest.raises(ValueError, match="non-empty string"):
        get_nearby_geohashes(None)  # type: ignore
