from src.models import Location, Driver, Ride
from src.simulator import Simulator
from src.strategies.weighted import WeightedScoreStrategy


def test_get_candidate_drivers_filters_by_vehicle_type():
    pickup = Location(10.0, 10.0)
    dropoff = Location(10.1, 10.1)

    ride = Ride(
        id="r1",
        pickup=pickup,
        dropoff=dropoff,
        request_time_str="2024-01-01T00:00:00Z",
        passenger_rating=4.0,
    )
    # requirement: needs an SUV
    ride.vehicle_type = "suv"

    driver_private = Driver(
        id="d1",
        name="PrivateDriver",
        rating=3.0,
        vehicle_type="private",
        current_location=Location(10.0, 10.0),
    )

    driver_suv = Driver(
        id="d2",
        name="SuvDriver",
        rating=5.0,
        vehicle_type="suv",
        current_location=Location(10.0, 10.0),
    )

    sim = Simulator(WeightedScoreStrategy())
    sim.add_driver(driver_private)
    sim.add_driver(driver_suv)

    candidates = sim.get_candidate_drivers(ride)

    assert len(candidates) == 1
    assert candidates[0].id == "d2"


def test_weighted_score_strategy_prefers_better_driver():
    pickup = Location(10.0, 10.0)
    dropoff = Location(10.05, 10.05)

    ride = Ride(
        id="r2",
        pickup=pickup,
        dropoff=dropoff,
        request_time_str="2024-01-01T00:00:00Z",
        passenger_rating=4.0,
        vehicle_type="private",
    )

    closer_lower_rating = Driver(
        id="d3",
        name="CloseLowerRating",
        rating=3.5,
        vehicle_type="private",
        current_location=Location(10.01, 10.01),
    )
    farther_better_rating = Driver(
        id="d4",
        name="FarBetterRating",
        rating=5.0,
        vehicle_type="private",
        current_location=Location(10.05, 10.05),
    )

    strategy = WeightedScoreStrategy()
    winner = strategy.match(ride, [closer_lower_rating, farther_better_rating])

    assert winner is closer_lower_rating
