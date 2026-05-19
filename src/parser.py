"""Input parser and output reporter for the ride-share simulator."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple

from jsonschema import ValidationError, validate

from src.logic import timestamp_str_to_seconds
from src.models import Driver, Location, Ride

logger = logging.getLogger(__name__)

DRIVER_SCHEMA = {
    "type": "object",
    "required": ["id", "name", "rating", "vehicle_type", "current_location"],
    "properties": {
        "id": {"type": "string", "minLength": 1},
        "name": {"type": "string", "minLength": 2},
        "rating": {"type": "number", "minimum": 1.0, "maximum": 5.0},
        "vehicle_type": {"type": "string", "enum": ["private", "suv"]},
        "current_location": {
            "type": "object",
            "required": ["lat", "lon"],
            "properties": {
                "lat": {"type": "number", "minimum": -90.0, "maximum": 90.0},
                "lon": {"type": "number", "minimum": -180.0, "maximum": 180.0},
            },
            "additionalProperties": False,
        },
    },
    "additionalProperties": False,
}

RIDE_SCHEMA = {
    "type": "object",
    "required": ["id", "pickup", "dropoff", "request_time", "passenger_rating"],
    "properties": {
        "id": {"type": "string", "minLength": 1},
        "pickup": {
            "type": "object",
            "required": ["lat", "lon"],
            "properties": {
                "lat": {"type": "number", "minimum": -90.0, "maximum": 90.0},
                "lon": {"type": "number", "minimum": -180.0, "maximum": 180.0},
            },
            "additionalProperties": False,
        },
        "dropoff": {
            "type": "object",
            "required": ["lat", "lon"],
            "properties": {
                "lat": {"type": "number", "minimum": -90.0, "maximum": 90.0},
                "lon": {"type": "number", "minimum": -180.0, "maximum": 180.0},
            },
            "additionalProperties": False,
        },
        "request_time": {
            "type": "string",
            "pattern": r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(Z|[+-]\d{2}:\d{2})$",
        },
        "passenger_rating": {"type": "number", "minimum": 1.0, "maximum": 5.0},
        "vehicle_type": {"type": "string", "enum": ["private", "suv"]},
    },
    "additionalProperties": False,
}


def _validate_record(record: dict, schema: dict) -> bool:
    try:
        validate(instance=record, schema=schema)
        return True
    except ValidationError as error:
        logger.warning("Skipping invalid record: %s", error.message)
        return False


def _parse_request_time(value: object) -> float:
    if not isinstance(value, str):
        raise ValueError("request_time must use ISO-8601 format.")
    return timestamp_str_to_seconds(value)


def parse_input_json(filepath: str) -> Tuple[List[Driver], List[Ride]]:
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {filepath}")

    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    drivers: List[Driver] = []
    rides: List[Ride] = []

    for driver_record in data.get("drivers", []):
        if not _validate_record(driver_record, DRIVER_SCHEMA):
            continue

        try:
            current_location = Location(
                lat=float(driver_record["current_location"]["lat"]),
                lon=float(driver_record["current_location"]["lon"]),
            )
            driver = Driver(
                id=driver_record["id"],
                name=driver_record["name"],
                rating=float(driver_record["rating"]),
                vehicle_type=driver_record["vehicle_type"],
                current_location=current_location,
            )
            drivers.append(driver)
        except Exception as error:
            logger.warning("Skipping invalid driver record: %s", error)
            continue

    for ride_record in data.get("rides", []):
        if not _validate_record(ride_record, RIDE_SCHEMA):
            continue

        pickup = Location(
            lat=float(ride_record["pickup"]["lat"]),
            lon=float(ride_record["pickup"]["lon"]),
        )
        dropoff = Location(
            lat=float(ride_record["dropoff"]["lat"]),
            lon=float(ride_record["dropoff"]["lon"]),
        )

        try:
            ride = Ride(
                id=ride_record["id"],
                pickup=pickup,
                dropoff=dropoff,
                request_time_seconds=_parse_request_time(ride_record["request_time"]),
                passenger_rating=float(ride_record["passenger_rating"]),
                vehicle_type=ride_record.get("vehicle_type", "private"),
            )
            rides.append(ride)
        except Exception as error:
            logger.warning("Skipping invalid ride record: %s", error)

    return drivers, rides


def generate_report(simulator_results: Dict) -> Dict:
    metrics = simulator_results.get("metrics", {})
    return {
        "assignments": simulator_results.get("assignments", []),
        "unassigned": simulator_results.get("unassigned", []),
        "metrics": {
            "global_average_arrival_time": metrics.get("global_average_arrival_time", 0.0),
            "total_assigned": metrics.get("total_assigned", 0),
            "total_unassigned": metrics.get("total_unassigned", 0),
            "driver_stats": metrics.get("driver_stats", []),
        },
    }


def save_to_json(report: Dict, output_filepath: str) -> None:
    output_path = Path(output_filepath)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
