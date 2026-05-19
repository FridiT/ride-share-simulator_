"""Generate a sample JSON input file for the Ride Share Simulator.

This script is a development helper for creating driver and ride datasets
that can be used for local testing and verification.
"""

from __future__ import annotations

import argparse
import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List


CITY_CENTER_LAT = 32.0853
CITY_CENTER_LON = 34.7818
DRIVER_DELTA_DEGREES = 0.08
RIDE_DELTA_DEGREES = 0.10


def _random_location(lat_center: float, lon_center: float, delta: float) -> Dict[str, float]:
    return {
        "lat": round(lat_center + random.uniform(-delta, delta), 6),
        "lon": round(lon_center + random.uniform(-delta, delta), 6),
    }


def _random_rating() -> float:
    return round(random.uniform(1.0, 5.0), 1)


def _random_vehicle_type() -> str:
    return random.choices(["private", "suv"], weights=[0.75, 0.25], k=1)[0]


def _build_drivers(count: int) -> List[Dict[str, Any]]:
    drivers: List[Dict[str, Any]] = []
    for index in range(1, count + 1):
        drivers.append(
            {
                "id": f"driver_{index}",
                "name": f"Driver {index}",
                "rating": _random_rating(),
                "vehicle_type": _random_vehicle_type(),
                "current_location": _random_location(CITY_CENTER_LAT, CITY_CENTER_LON, DRIVER_DELTA_DEGREES),
            }
        )
    return drivers


def _build_rides(count: int, start_time: datetime) -> List[Dict[str, Any]]:
    rides: List[Dict[str, Any]] = []
    current_time = start_time

    for index in range(1, count + 1):
        pickup = _random_location(CITY_CENTER_LAT, CITY_CENTER_LON, RIDE_DELTA_DEGREES)
        dropoff = _random_location(CITY_CENTER_LAT, CITY_CENTER_LON, RIDE_DELTA_DEGREES)
        rides.append(
            {
                "id": f"ride_{index}",
                "pickup": pickup,
                "dropoff": dropoff,
                "request_time": round(current_time.timestamp(), 2),
                "passenger_rating": _random_rating(),
                "vehicle_type": _random_vehicle_type(),
            }
        )
        current_time += timedelta(seconds=random.randint(5, 20))

    return rides


def generate_sample_input(drivers: int, rides: int, output_path: Path) -> None:
    payload = {
        "drivers": _build_drivers(drivers),
        "rides": _build_rides(rides, datetime(2025, 1, 1, 8, 0, tzinfo=timezone.utc)),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate development JSON input for the Ride Share Simulator.")
    parser.add_argument(
        "--output",
        default="data/input_dev.json",
        help="Path to write the generated JSON input file.",
    )
    parser.add_argument(
        "--drivers",
        type=int,
        default=30,
        help="Number of drivers to generate.",
    )
    parser.add_argument(
        "--rides",
        type=int,
        default=70,
        help="Number of rides to generate.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for deterministic sample generation.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    random.seed(args.seed)

    output_path = Path(args.output)
    generate_sample_input(args.drivers, args.rides, output_path)
    print(f"Generated sample input: {output_path} ({args.drivers} drivers, {args.rides} rides)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
