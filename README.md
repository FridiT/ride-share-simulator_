# Ride Share Simulator

Simulator for matching ride requests to available drivers using configurable strategies.

## Project Overview

This project implements a discrete-event ride-share simulator that:
- loads driver and ride request data from a JSON file
- schedules drivers to rides using a pluggable strategy
- tracks driver availability, trip timings, and assignment metrics
- outputs a JSON report with assignments and performance statistics

## Installation

Recommended Python version: 3.10+

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
      "request_time": 1716145200,
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
    {"timestamp_str": "2024-05-19T10:30:00Z", "ride_id": "ride_1", "driver_id": "driver_1"}
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
- `scripts/generate_dev_input.py` is a dev utility that generates sample input for local testing.
- Input JSON is expected to contain both `drivers` and `rides` arrays in one document.
- Internal time is represented as Unix seconds; external timestamps may be numeric or ISO-8601.
- Rides are sorted before simulation by `(request_time_seconds, distance, ride_id)`:
  - `request_time_seconds` ensures chronological processing,
  - `distance` prioritizes shorter trips to improve responsiveness and free drivers sooner,
  - `ride_id` makes ordering deterministic when other values tie.
- Driver availability is modeled by data structure membership, not a separate availability flag.
- Only drivers within the 9-cell geohash neighborhood and within `MAX_PICKUP_DISTANCE_KM` are considered.
- Weighted matching normalizes distance and rating difference into a comparable score.
- Invalid input records are skipped with warnings rather than causing a fatal error.

## Notes

- Drivers are considered available when stored in the spatial index.
- The simulator advances time only to the next ride arrival or driver release event.
- A ride is marked unassigned after timing out or if no driver is available by simulation end.
