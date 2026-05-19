import json

from src.parser import generate_report, parse_input_json, save_to_json
from src.models import Driver, Ride


def test_parse_input_json_valid(tmp_path):
    payload = {
        "drivers": [
            {
                "id": "d1",
                "name": "Alice",
                "rating": 4.5,
                "vehicle_type": "private",
                "current_location": {"lat": 10.0, "lon": 10.0},
            }
        ],
        "rides": [
            {
                "id": "r1",
                "pickup": {"lat": 10.0, "lon": 10.0},
                "dropoff": {"lat": 10.1, "lon": 10.1},
                "request_time": "2024-01-01T00:00:00Z",
                "passenger_rating": 5.0,
                "vehicle_type": "private",
            }
        ],
    }

    file_path = tmp_path / "input.json"
    file_path.write_text(json.dumps(payload), encoding="utf-8")

    drivers, rides = parse_input_json(str(file_path))

    assert len(drivers) == 1
    assert drivers[0].id == "d1"
    assert drivers[0].vehicle_type == "private"

    assert len(rides) == 1
    assert rides[0].id == "r1"
    assert rides[0].vehicle_type == "private"


def test_parse_input_json_skips_invalid_records(tmp_path):
    payload = {
        "drivers": [
            {
                "id": "d1",
                "name": "Alice",
                "rating": 4.5,
                "vehicle_type": "private",
                "current_location": {"lat": 10.0, "lon": 10.0},
            },
            {
                "id": "d2",
                "name": "Bob",
                "rating": 6.0,
                "vehicle_type": "private",
                "current_location": {"lat": 10.0, "lon": 10.0},
            },
        ],
        "rides": [
            {
                "id": "r1",
                "pickup": {"lat": 10.0, "lon": 10.0},
                "dropoff": {"lat": 10.1, "lon": 10.1},
                "request_time": "2024-01-01T00:00:00Z",
                "passenger_rating": 5.0,
                "vehicle_type": "private",
            },
            {
                "id": "r2",
                "pickup": {"lat": 10.0, "lon": 10.0},
                "dropoff": {"lat": 10.1, "lon": 10.1},
                "request_time": "2024-01-01_00-00-00",
                "passenger_rating": 5.0,
                "vehicle_type": "private",
            },
        ],
    }

    file_path = tmp_path / "input.json"
    file_path.write_text(json.dumps(payload), encoding="utf-8")

    drivers, rides = parse_input_json(str(file_path))

    assert len(drivers) == 1
    assert drivers[0].id == "d1"
    assert len(rides) == 1
    assert rides[0].id == "r1"


def test_parse_input_json_skips_invalid_timestamp_string_request_time(tmp_path):
    payload = {
        "drivers": [],
        "rides": [
            {
                "id": "r_bad_ts",
                "pickup": {"lat": 10.0, "lon": 10.0},
                "dropoff": {"lat": 10.1, "lon": 10.1},
                "request_time": "not-a-timestamp",
                "passenger_rating": 4.0,
                "vehicle_type": "private",
            }
        ],
    }

    file_path = tmp_path / "input_bad_ts.json"
    file_path.write_text(json.dumps(payload), encoding="utf-8")

    _, rides = parse_input_json(str(file_path))

    assert rides == []


def test_parse_input_json_skips_numeric_request_time(tmp_path):
    payload = {
        "drivers": [],
        "rides": [
            {
                "id": "r_num",
                "pickup": {"lat": 10.0, "lon": 10.0},
                "dropoff": {"lat": 10.1, "lon": 10.1},
                "request_time": 1704067200.0,
                "passenger_rating": 4.0,
                "vehicle_type": "private",
            }
        ],
    }

    file_path = tmp_path / "input_num_ts.json"
    file_path.write_text(json.dumps(payload), encoding="utf-8")

    _, rides = parse_input_json(str(file_path))

    assert rides == []


def test_generate_report_and_save_to_json(tmp_path):
    results = {
        "assignments": [{"timestamp": "2024-01-01T00:00:00Z", "ride_id": "r1", "driver_id": "d1"}],
        "unassigned": ["r2"],
        "metrics": {
            "global_average_arrival_time": 2.5,
            "total_assigned": 1,
            "total_unassigned": 1,
            "driver_stats": [{"driver_id": "d1", "ride_count": 1, "average_arrival_time": 2.5}],
        },
    }
    report = generate_report(results)

    assert report["assignments"][0]["ride_id"] == "r1"
    assert report["metrics"]["global_average_arrival_time"] == 2.5

    output_file = tmp_path / "report.json"
    save_to_json(report, str(output_file))
    assert output_file.exists()
    loaded = json.loads(output_file.read_text(encoding="utf-8"))
    assert loaded["metrics"]["total_assigned"] == 1
