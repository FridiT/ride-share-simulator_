import math

import pytest

from src.models import Location, Driver, Ride
from src.logic import BASE_SPEED_KMH


def test_distance_to_same_location_is_zero() -> None:
    # Test that the distance from a location to itself is zero
    location = Location(lat=51.5074, lon=-0.1278)
    assert math.isclose(location.distance_to(location), 0.0, abs_tol=1e-9)


def test_distance_to_known_equatorial_degree() -> None:
    # Test the distance between two points on the equator that are 1 degree apart in longitude
    location_a = Location(lat=0.0, lon=0.0)
    location_b = Location(lat=0.0, lon=1.0)

    distance_km = location_a.distance_to(location_b)
    assert pytest.approx(distance_km, rel=1e-3) == 111.195


def test_to_geohash_default_precision() -> None:
    # Test the default precision of the geohash
    location = Location(lat=37.7749, lon=-122.4194)
    geohash_default = location.to_geohash()
    geohash_precision_5 = location.to_geohash(precision=5)

    assert isinstance(geohash_default, str)
    assert len(geohash_default) == 6
    assert geohash_default.startswith(geohash_precision_5)


def test_to_geohash_invalid_precision_raises_value_error() -> None:
    # Test that providing an invalid precision (e.g., 0) raises a ValueError
    location = Location(lat=0.0, lon=0.0)

    with pytest.raises(ValueError):
        location.to_geohash(precision=0)


# ==================== Driver Tests ====================
# todo: the Driver Model should validate that the vehicle type is one of the allowed types
# those test should be failed yet because "sedan" is not an allowed vehicle type
# those validation are verified in the Schema Json, add it to the model too (drivers and rides)

def test_driver_creation_valid() -> None:
    # Test creating a Driver with valid fields and ensure they are set correctly
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
    # Test that providing an empty id raises a ValueError
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
    # Test that providing a rating below the minimum (e.g., 0.5) raises a ValueError
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
    # Test that providing a rating above the maximum (e.g., 5.5) raises a ValueError
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
    # Test that providing an empty vehicle_type raises a ValueError
    location = Location(lat=0.0, lon=0.0)

    with pytest.raises(ValueError, match="vehicle_type cannot be empty"):
        Driver(
            id="d4",
            name="Eve",
            rating=4.0,
            vehicle_type="",
            current_location=location,
        )

# todo the avilable_at should be a timestamp string in ISO format instead of a float
def test_driver_creation_invalid_available_at() -> None:
    # Test that providing a negative available_at time raises a ValueError
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
    # Test that the driver's location can be updated correctly
    location1 = Location(lat=51.5074, lon=-0.1278)
    location2 = Location(lat=48.8566, lon=2.3522)
    driver = Driver(
        id="d6", name="Grace", rating=4.0, vehicle_type="sedan", current_location=location1
    )

    driver.update_location(location2)
    assert driver.current_location == location2


def test_driver_less_than_comparison() -> None:
    # Test that the less-than comparison between drivers works correctly based on available_at
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
    # Test the string representation of a Driver and ensure it contains key information
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
    # Test creating a Ride with valid fields and ensure they are set correctly
    pickup = Location(lat=51.5074, lon=-0.1278)
    dropoff = Location(lat=48.8566, lon=2.3522)
    ride = Ride(
        id="r1",
        pickup=pickup,
        dropoff=dropoff,
        request_time_seconds=1716066600.0,
        passenger_rating=4.0,
    )

    assert ride.id == "r1"
    assert ride.pickup == pickup
    assert ride.dropoff == dropoff
    assert ride.request_time_seconds == 1716066600.0
    assert ride.passenger_rating == 4.0


def test_ride_creation_invalid_id() -> None:
    # Test that providing an empty id raises a ValueError
    pickup = Location(lat=0.0, lon=0.0)
    dropoff = Location(lat=1.0, lon=1.0)

    with pytest.raises(ValueError, match="id cannot be empty"):
        Ride(
            id="",
            pickup=pickup,
            dropoff=dropoff,
            request_time_seconds=1716066600.0,
            passenger_rating=3.5,
        )


def test_ride_creation_invalid_rating_too_low() -> None:
    # Test that providing a rating below the minimum raises a ValueError
    pickup = Location(lat=0.0, lon=0.0)
    dropoff = Location(lat=1.0, lon=1.0)

    with pytest.raises(ValueError, match="rating must be between"):
        Ride(
            id="r2",
            pickup=pickup,
            dropoff=dropoff,
            request_time_seconds=1716066600.0,
            passenger_rating=0.5,
        )


def test_ride_creation_invalid_rating_too_high() -> None:
    # Test that providing a rating above the maximum raises a ValueError
    pickup = Location(lat=0.0, lon=0.0)
    dropoff = Location(lat=1.0, lon=1.0)

    with pytest.raises(ValueError, match="rating must be between"):
        Ride(
            id="r3",
            pickup=pickup,
            dropoff=dropoff,
            request_time_seconds=1716066600.0,
            passenger_rating=5.5,
        )


def test_ride_creation_invalid_request_time() -> None:
    # Test that providing an invalid request time raises a ValueError
    pickup = Location(lat=0.0, lon=0.0)
    dropoff = Location(lat=1.0, lon=1.0)

    with pytest.raises(ValueError, match="Ride request_time_seconds must be a non-negative finite timestamp"):
        Ride(
            id="r4",
            pickup=pickup,
            dropoff=dropoff,
            request_time_seconds=float("nan"),
            passenger_rating=3.0,
        )


def test_ride_calculate_distance() -> None:
    # Test the distance calculation between two locations
    pickup = Location(lat=0.0, lon=0.0)
    dropoff = Location(lat=0.0, lon=1.0)
    ride = Ride(
        id="r5",
        pickup=pickup,
        dropoff=dropoff,
        request_time_seconds=1716066600.0,
        passenger_rating=3.5,
    )

    distance = ride.calculate_distance()
    assert pytest.approx(distance, rel=1e-3) == 111.195


def test_ride_calculate_estimated_time_with_default_speed() -> None:
    # Test the estimated time calculation using the default speed
    pickup = Location(lat=0.0, lon=0.0)
    dropoff = Location(lat=0.0, lon=1.0)
    ride = Ride(
        id="r6",
        pickup=pickup,
        dropoff=dropoff,
        request_time_seconds=1716066600.0,
        passenger_rating=4.0,
    )

    estimated_time = ride.calculate_estimated_time()
    expected_seconds = (111.195 / BASE_SPEED_KMH) * 3600
    assert pytest.approx(estimated_time, rel=1e-3) == expected_seconds


def test_ride_calculate_estimated_time_with_custom_speed() -> None:
    # Test the estimated time calculation using a custom speed
    pickup = Location(lat=0.0, lon=0.0)
    dropoff = Location(lat=0.0, lon=1.0)
    ride = Ride(
        id="r7",
        pickup=pickup,
        dropoff=dropoff,
        request_time_seconds=1716066600.0,
        passenger_rating=3.8,
    )

    estimated_time = ride.calculate_estimated_time(speed_kmh=60.0)
    expected_seconds = (111.195 / 60.0) * 3600
    assert pytest.approx(estimated_time, rel=1e-3) == expected_seconds


def test_ride_calculate_estimated_time_invalid_speed() -> None:
    # Test that providing an invalid speed (e.g., 0) raises a ValueError
    pickup = Location(lat=0.0, lon=0.0)
    dropoff = Location(lat=1.0, lon=1.0)
    ride = Ride(
        id="r8",
        pickup=pickup,
        dropoff=dropoff,
        request_time_seconds=1716066600.0,
        passenger_rating=4.2,
    )

    with pytest.raises(ValueError, match="Speed must be positive"):
        ride.calculate_estimated_time(speed_kmh=0.0)


def test_ride_repr() -> None:
    # Test the string representation of a Ride and ensure it contains key information
    pickup = Location(lat=51.5074, lon=-0.1278)
    dropoff = Location(lat=48.8566, lon=2.3522)
    ride = Ride(
        id="r9",
        pickup=pickup,
        dropoff=dropoff,
        request_time_seconds=1716066600.0,
        passenger_rating=4.5,
    )

    repr_str = repr(ride)
    assert "r9" in repr_str
    assert "51.5074" in repr_str or "51" in repr_str
    assert "request_time_seconds=1716066600.0" in repr_str
    assert "4.5" in repr_str


def test_ride_request_time_conversion() -> None:
    # Todo: this test not necessary here yet, till we move the convertion request time into Model 
    # Test that the request time is correctly converted to seconds and stored in the Ride object
    pickup = Location(lat=0.0, lon=0.0)
    dropoff = Location(lat=1.0, lon=1.0)
    timestamp_seconds = 1716066600.0
    ride = Ride(
        id="r10",
        pickup=pickup,
        dropoff=dropoff,
        request_time_seconds=timestamp_seconds,
        passenger_rating=3.5,
    )

    assert ride.request_time_seconds == timestamp_seconds

