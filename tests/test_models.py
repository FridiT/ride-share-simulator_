import math

import pytest

from src.models import Location, Driver, Ride
from src.logic import BASE_SPEED_KMH, iso8601_to_seconds


def test_distance_to_same_location_is_zero() -> None:
    location = Location(lat=51.5074, lon=-0.1278)
    assert math.isclose(location.distance_to(location), 0.0, abs_tol=1e-9)


def test_distance_to_known_equatorial_degree() -> None:
    location_a = Location(lat=0.0, lon=0.0)
    location_b = Location(lat=0.0, lon=1.0)

    distance_km = location_a.distance_to(location_b)
    assert pytest.approx(distance_km, rel=1e-3) == 111.195


def test_to_geohash_default_precision() -> None:
    location = Location(lat=37.7749, lon=-122.4194)
    geohash_default = location.to_geohash()
    geohash_precision_5 = location.to_geohash(precision=5)

    assert isinstance(geohash_default, str)
    assert len(geohash_default) == 6
    assert geohash_default.startswith(geohash_precision_5)


def test_to_geohash_invalid_precision_raises_value_error() -> None:
    location = Location(lat=0.0, lon=0.0)

    with pytest.raises(ValueError):
        location.to_geohash(precision=0)


# ==================== Driver Tests ====================


def test_driver_creation_valid() -> None:
    location = Location(lat=51.5074, lon=-0.1278)
    driver = Driver(
        id="d1",
        name="Alice",
        rating=4.5,
        vehicle_type="sedan",
        current_location=location,
        available_at=100.0,
    )

    assert driver.id == "d1"
    assert driver.name == "Alice"
    assert driver.rating == 4.5
    assert driver.vehicle_type == "sedan"
    assert driver.current_location == location
    assert driver.available_at == 100.0


def test_driver_creation_invalid_id() -> None:
    location = Location(lat=0.0, lon=0.0)

    with pytest.raises(ValueError, match="id cannot be empty"):
        Driver(
            id="",
            name="Bob",
            rating=3.5,
            vehicle_type="suv",
            current_location=location,
        )


def test_driver_creation_invalid_rating_too_low() -> None:
    location = Location(lat=0.0, lon=0.0)

    with pytest.raises(ValueError, match="rating must be between"):
        Driver(
            id="d2",
            name="Charlie",
            rating=0.5,
            vehicle_type="sedan",
            current_location=location,
        )


def test_driver_creation_invalid_rating_too_high() -> None:
    location = Location(lat=0.0, lon=0.0)

    with pytest.raises(ValueError, match="rating must be between"):
        Driver(
            id="d3",
            name="Diana",
            rating=5.5,
            vehicle_type="sedan",
            current_location=location,
        )


def test_driver_creation_invalid_vehicle_type() -> None:
    location = Location(lat=0.0, lon=0.0)

    with pytest.raises(ValueError, match="vehicle_type cannot be empty"):
        Driver(
            id="d4",
            name="Eve",
            rating=4.0,
            vehicle_type="",
            current_location=location,
        )


def test_driver_creation_invalid_available_at() -> None:
    location = Location(lat=0.0, lon=0.0)

    with pytest.raises(ValueError, match="available_at cannot be negative"):
        Driver(
            id="d5",
            name="Frank",
            rating=3.0,
            vehicle_type="sedan",
            current_location=location,
            available_at=-10.0,
        )


def test_driver_update_location() -> None:
    location1 = Location(lat=51.5074, lon=-0.1278)
    location2 = Location(lat=48.8566, lon=2.3522)
    driver = Driver(
        id="d6", name="Grace", rating=4.0, vehicle_type="sedan", current_location=location1
    )

    driver.update_location(location2)
    assert driver.current_location == location2


def test_driver_less_than_comparison() -> None:
    location = Location(lat=0.0, lon=0.0)
    driver1 = Driver(
        id="d7",
        name="Henry",
        rating=3.5,
        vehicle_type="sedan",
        current_location=location,
        available_at=100.0,
    )
    driver2 = Driver(
        id="d8",
        name="Iris",
        rating=4.0,
        vehicle_type="sedan",
        current_location=location,
        available_at=200.0,
    )

    assert driver1 < driver2
    assert not driver2 < driver1


def test_driver_repr() -> None:
    location = Location(lat=51.5074, lon=-0.1278)
    driver = Driver(
        id="d9",
        name="Jack",
        rating=4.2,
        vehicle_type="sedan",
        current_location=location,
        available_at=150.0,
    )

    repr_str = repr(driver)
    assert "d9" in repr_str
    assert "Jack" in repr_str
    assert "4.2" in repr_str
    assert "sedan" in repr_str


# ==================== Ride Tests ====================


def test_ride_creation_valid() -> None:
    pickup = Location(lat=51.5074, lon=-0.1278)
    dropoff = Location(lat=48.8566, lon=2.3522)
    ride = Ride(
        id="r1",
        pickup=pickup,
        dropoff=dropoff,
        request_time_str="2024-05-19T10:30:00Z",
        passenger_rating=4.0,
    )

    assert ride.id == "r1"
    assert ride.pickup == pickup
    assert ride.dropoff == dropoff
    assert ride.request_time_str == "2024-05-19T10:30:00Z"
    assert ride.passenger_rating == 4.0
    assert ride.request_time_seconds > 0.0


def test_ride_creation_invalid_id() -> None:
    pickup = Location(lat=0.0, lon=0.0)
    dropoff = Location(lat=1.0, lon=1.0)

    with pytest.raises(ValueError, match="id cannot be empty"):
        Ride(
            id="",
            pickup=pickup,
            dropoff=dropoff,
            request_time_str="2024-05-19T10:30:00Z",
            passenger_rating=3.5,
        )


def test_ride_creation_invalid_rating_too_low() -> None:
    pickup = Location(lat=0.0, lon=0.0)
    dropoff = Location(lat=1.0, lon=1.0)

    with pytest.raises(ValueError, match="rating must be between"):
        Ride(
            id="r2",
            pickup=pickup,
            dropoff=dropoff,
            request_time_str="2024-05-19T10:30:00Z",
            passenger_rating=0.5,
        )


def test_ride_creation_invalid_rating_too_high() -> None:
    pickup = Location(lat=0.0, lon=0.0)
    dropoff = Location(lat=1.0, lon=1.0)

    with pytest.raises(ValueError, match="rating must be between"):
        Ride(
            id="r3",
            pickup=pickup,
            dropoff=dropoff,
            request_time_str="2024-05-19T10:30:00Z",
            passenger_rating=5.5,
        )


def test_ride_creation_invalid_request_time() -> None:
    pickup = Location(lat=0.0, lon=0.0)
    dropoff = Location(lat=1.0, lon=1.0)

    with pytest.raises(ValueError, match="Invalid request_time_str"):
        Ride(
            id="r4",
            pickup=pickup,
            dropoff=dropoff,
            request_time_str="not-a-timestamp",
            passenger_rating=3.0,
        )


def test_ride_calculate_distance() -> None:
    pickup = Location(lat=0.0, lon=0.0)
    dropoff = Location(lat=0.0, lon=1.0)
    ride = Ride(
        id="r5",
        pickup=pickup,
        dropoff=dropoff,
        request_time_str="2024-05-19T10:30:00Z",
        passenger_rating=3.5,
    )

    distance = ride.calculate_distance()
    assert pytest.approx(distance, rel=1e-3) == 111.195


def test_ride_calculate_estimated_time_with_default_speed() -> None:
    pickup = Location(lat=0.0, lon=0.0)
    dropoff = Location(lat=0.0, lon=1.0)
    ride = Ride(
        id="r6",
        pickup=pickup,
        dropoff=dropoff,
        request_time_str="2024-05-19T10:30:00Z",
        passenger_rating=4.0,
    )

    estimated_time = ride.calculate_estimated_time()
    expected_seconds = (111.195 / BASE_SPEED_KMH) * 3600
    assert pytest.approx(estimated_time, rel=1e-3) == expected_seconds


def test_ride_calculate_estimated_time_with_custom_speed() -> None:
    pickup = Location(lat=0.0, lon=0.0)
    dropoff = Location(lat=0.0, lon=1.0)
    ride = Ride(
        id="r7",
        pickup=pickup,
        dropoff=dropoff,
        request_time_str="2024-05-19T10:30:00Z",
        passenger_rating=3.8,
    )

    estimated_time = ride.calculate_estimated_time(speed_kmh=60.0)
    expected_seconds = (111.195 / 60.0) * 3600
    assert pytest.approx(estimated_time, rel=1e-3) == expected_seconds


def test_ride_calculate_estimated_time_invalid_speed() -> None:
    pickup = Location(lat=0.0, lon=0.0)
    dropoff = Location(lat=1.0, lon=1.0)
    ride = Ride(
        id="r8",
        pickup=pickup,
        dropoff=dropoff,
        request_time_str="2024-05-19T10:30:00Z",
        passenger_rating=4.2,
    )

    with pytest.raises(ValueError, match="Speed must be positive"):
        ride.calculate_estimated_time(speed_kmh=0.0)


def test_ride_repr() -> None:
    pickup = Location(lat=51.5074, lon=-0.1278)
    dropoff = Location(lat=48.8566, lon=2.3522)
    ride = Ride(
        id="r9",
        pickup=pickup,
        dropoff=dropoff,
        request_time_str="2024-05-19T10:30:00Z",
        passenger_rating=4.5,
    )

    repr_str = repr(ride)
    assert "r9" in repr_str
    assert "51.5074" in repr_str or "51" in repr_str
    assert "2024-05-19T10:30:00Z" in repr_str
    assert "4.5" in repr_str


def test_ride_request_time_conversion() -> None:
    pickup = Location(lat=0.0, lon=0.0)
    dropoff = Location(lat=1.0, lon=1.0)
    timestamp_str = "2024-05-19T10:30:00Z"
    ride = Ride(
        id="r10",
        pickup=pickup,
        dropoff=dropoff,
        request_time_str=timestamp_str,
        passenger_rating=3.5,
    )

    expected_seconds = iso8601_to_seconds(timestamp_str)
    assert ride.request_time_seconds == expected_seconds

