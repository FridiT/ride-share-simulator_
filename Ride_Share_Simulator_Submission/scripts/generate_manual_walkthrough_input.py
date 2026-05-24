"""Generate a tiny deterministic input for manual end-to-end simulator walkthrough.

The generated dataset is intentionally small but covers:
- same-timestamp ride collision
- pending queue behavior
- timeout in queue (> 300 seconds)
- unassigned ride due to pickup radius constraint
- queued ride that is eventually assigned when a driver is released
"""

from __future__ import annotations

import json
from pathlib import Path


def build_payload() -> dict:
    base_lat = 32.0853
    base_lon = 34.7818

    return {
        "drivers": [
            {
                "id": "d_private",
                "name": "Dana",
                "rating": 4.8,
                "vehicle_type": "private",
                "current_location": {"lat": base_lat, "lon": base_lon},
            },
            {
                "id": "d_suv",
                "name": "Shai",
                "rating": 4.6,
                "vehicle_type": "suv",
                "current_location": {"lat": base_lat, "lon": base_lon},
            },
        ],
        "rides": [
            {
                "id": "r1_private_long",
                "pickup": {"lat": base_lat, "lon": base_lon},
                "dropoff": {"lat": 32.1153, "lon": 34.7818},
                "request_time": "2025-01-01T08:00:00Z",
                "passenger_rating": 4.7,
                "vehicle_type": "private",
            },
            {
                "id": "r2_private_collision",
                "pickup": {"lat": base_lat, "lon": base_lon},
                "dropoff": {"lat": 32.1153, "lon": 34.7818},
                "request_time": "2025-01-01T08:00:00Z",
                "passenger_rating": 4.5,
                "vehicle_type": "private",
            },
            {
                "id": "r3_suv_long",
                "pickup": {"lat": base_lat, "lon": base_lon},
                "dropoff": {"lat": 32.1053, "lon": 34.7818},
                "request_time": "2025-01-01T08:00:00Z",
                "passenger_rating": 4.2,
                "vehicle_type": "suv",
            },
            {
                "id": "r4_far_out_of_radius",
                "pickup": {"lat": 32.2853, "lon": 34.7818},
                "dropoff": {"lat": 32.2953, "lon": 34.7918},
                "request_time": "2025-01-01T08:01:00Z",
                "passenger_rating": 4.0,
                "vehicle_type": "private",
            },
            {
                "id": "r5_wait_then_assign",
                "pickup": {"lat": 32.0859, "lon": 34.7822},
                "dropoff": {"lat": 32.0900, "lon": 34.7850},
                "request_time": "2025-01-01T08:06:00Z",
                "passenger_rating": 4.4,
                "vehicle_type": "private",
            },
        ],
    }


def main() -> int:
    output_path = Path("data/manual_walkthrough_input.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    payload = build_payload()
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)

    print(f"Generated manual walkthrough input: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
