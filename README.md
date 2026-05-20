# Ride Share Simulator

Simulator for matching ride requests to available drivers using configurable strategies.

## Project Overview

This project implements a discrete-event ride-share simulator that:
- loads driver and ride request data from a JSON file
- schedules drivers to rides using a pluggable strategy
- tracks driver availability, trip timings, and assignment metrics
- outputs a JSON report with assignments and performance statistics

## Installation

Recommended Python version: 3.12+

1. Create and activate a virtual environment.

PowerShell:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Command Prompt (CMD):
```cmd
python -m venv .venv
.\.venv\Scripts\activate.bat
```

2. Install dependencies:
```cmd
pip install -r requirements.txt
```

Required packages:
- `pygeohash`
- `jsonschema`
- `pytest` (for running tests)

## Usage

Run the simulator from the repository root.

PowerShell:
```powershell
python main.py --input data/input.json --strategy weighted --output output/results.json --dev
```

Command Prompt (CMD):
```cmd
python main.py --input data/input.json --strategy weighted --output output/results.json --dev
```

### Generate Dev Input

Use the helper script to create sample data for local testing:

```cmd
python scripts/generate_input.py
```

The script writes a fresh file and overwrites existing output if it already exists.

### CLI options

- `--input`: Path to the input JSON file (default: `data/input.json`)
- `--strategy`: Matching strategy, either `weighted` or `shortest` (default: `weighted`)
- `--output`: Path to output JSON report (default: `output/results.json`)
- `--dev`: Enable console logging in addition to file logging

## Input Format

The input JSON file must include both `drivers` and `rides` arrays.

Example:

```json
{
  "drivers": [
    {
      "id": "driver_1",
      "name": "Alice",
      "rating": 4.8,
      "vehicle_type": "private",
      "current_location": {"lat": 32.0853, "lon": 34.7818}
    }
  ],
  "rides": [
    {
      "id": "ride_1",
      "pickup": {"lat": 32.066, "lon": 34.777},
      "dropoff": {"lat": 32.092, "lon": 34.789},
      "request_time": "2024-05-19T10:30:00Z",
      "passenger_rating": 4.5,
      "vehicle_type": "private"
    }
  ]
}
```

## Output Format

The output report is a JSON file with the following structure:

```json
{
  "assignments": [
    {"timestamp": "2024-05-19T10:30:00Z", "ride_id": "ride_1", "driver_id": "driver_1"}
  ],
  "unassigned": ["ride_2"],
  "metrics": {
    "global_average_arrival_time": 12.34,
    "total_assigned": 1,
    "total_unassigned": 1,
    "driver_stats": [
      {"driver_id": "driver_1", "ride_count": 1, "average_arrival_time": 12.34}
    ]
  }
}
```

## Strategy Options

- `weighted`: Uses a weighted score combining driver distance and passenger-driver rating compatibility.
- `shortest`: Chooses the driver closest to the pickup location.

## Logging

The simulator writes log files to the `logs/` directory.

- `--dev` mode also outputs logs to the console.
- Logs include INFO-level summaries and warning/error diagnostics.

## Assumptions and Design Decisions

- The main program expects an existing input JSON file and does not generate input data.
- `scripts/generate_input.py` is a helper utility that generates sample input data.
- Input JSON is expected to contain both `drivers` and `rides` arrays in one document.
- Internal time is represented as Unix seconds (float); external timestamps in input/output must use ISO-8601 with seconds and timezone information (for example `2024-05-19T10:30:00Z` or `2024-05-19T10:30:00+02:00`).
- Rides are sorted before simulation by `(request_time_seconds, distance, ride_id)`:
  - `request_time_seconds` ensures chronological processing,
  - `distance` prioritizes shorter trips to improve responsiveness and free drivers sooner,
  - `ride_id` makes ordering deterministic when other values tie.
- Driver availability is modeled by data structure membership, not a separate availability flag.
- Core runtime structures are: geohash availability index (`available_drivers_by_geohash`) for available drivers, min-heap (`busy_drivers`) ordered by `available_at` for busy drivers, and FIFO queue (`pending_rides`) for unmatched ride requests.
- Candidate search first scans the 9-cell geohash neighborhood as a spatial prefilter, then applies the configurable `MAX_PICKUP_DISTANCE_KM` radius as the actual pickup distance constraint.
- Ride requests time out only after exceeding 300 seconds (5 minutes) in the pending queue and are marked unassigned.
- Weighted matching uses `distance_weight=0.3` and `rating_weight=0.7`, with normalization for both components.
- Invalid input records are skipped with warnings rather than causing a fatal error.

## Notes

- Drivers are considered available when stored in the geohash availability index.
- The simulator advances time only to the next ride arrival or driver release event.
- A ride is marked unassigned after timing out or if no driver is available by simulation end.
