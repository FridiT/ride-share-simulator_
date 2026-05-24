from src.models import Location, Driver, Ride
from src.parser import parse_input_json
from src.simulator import Simulator
from src.strategies.shortest import ShortestDistanceStrategy
from src.strategies.weighted import WeightedScoreStrategy


def test_get_candidate_drivers_filters_by_vehicle_type():
    pickup = Location(10.0, 10.0)
    dropoff = Location(10.1, 10.1)

    ride = Ride(
        id="r1",
        pickup=pickup,
        dropoff=dropoff,
        request_time_seconds=1704067200.0,
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
        request_time_seconds=1704067200.0,
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


def test_shortest_distance_strategy_prefers_closest_driver():
    pickup = Location(10.0, 10.0)
    dropoff = Location(10.05, 10.05)

    ride = Ride(
        id="r_shortest",
        pickup=pickup,
        dropoff=dropoff,
        request_time_seconds=1704067200.0,
        passenger_rating=4.0,
        vehicle_type="private",
    )

    farther_driver = Driver(
        id="d_far",
        name="FarDriver",
        rating=5.0,
        vehicle_type="private",
        current_location=Location(10.08, 10.08),
    )
    closer_driver = Driver(
        id="d_close",
        name="CloseDriver",
        rating=3.0,
        vehicle_type="private",
        current_location=Location(10.01, 10.01),
    )

    strategy = ShortestDistanceStrategy()
    winner = strategy.match(ride, [farther_driver, closer_driver])

    assert winner is closer_driver


def test_simulator_assignment_timestamp_is_formatted_string():
    ride = Ride(
        id="r3",
        pickup=Location(10.0, 10.0),
        dropoff=Location(10.01, 10.01),
        request_time_seconds=1704067200.0,
        passenger_rating=4.0,
        vehicle_type="private",
    )
    driver = Driver(
        id="d5",
        name="Driver5",
        rating=4.2,
        vehicle_type="private",
        current_location=Location(10.0, 10.0),
    )

    sim = Simulator(WeightedScoreStrategy())
    sim.add_driver(driver)

    results = sim.run([ride])

    assert len(results["assignments"]) == 1
    assert results["assignments"][0]["timestamp"] == "2024-01-01T00:00:00Z"


def test_manual_walkthrough_input_produces_expected_regression_outcome():
    drivers, rides = parse_input_json("data/manual_walkthrough_input.json")
    rides.sort(key=lambda ride: (ride.request_time_seconds, ride.calculate_distance(), ride.id))

    sim = Simulator(WeightedScoreStrategy())
    for driver in drivers:
        sim.add_driver(driver)

    results = sim.run(rides)

    assigned_pairs = [(entry["ride_id"], entry["driver_id"]) for entry in results["assignments"]]
    assert assigned_pairs == [
        ("r3_suv_long", "d_suv"),
        ("r1_private_long", "d_private"),
        ("r5_wait_then_assign", "d_private"),
    ]
    assert results["unassigned"] == ["r2_private_collision", "r4_far_out_of_radius"]
