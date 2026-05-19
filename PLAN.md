# Ride Share Simulator - Detailed Implementation Plan

## Phase 1: Project Structure & Setup [DONE] ✓

### 1.1 Create Directory Structure [DONE] ✓
**Action:** Create the following directories at project root
```
Ride_Share_Simulator/
├── src/
│   └── strategies/
├── tests/
├── data/
├── scripts/
├── output/
├── logs/
└── README.md
```

### 1.2 Create Python Package Initialization [DONE] ✓
**File:** `src/__init__.py`
- Empty file to mark `src` as a Python package

**File:** `src/strategies/__init__.py`
- Empty file to mark `src/strategies` as a Python subpackage

**File:** `tests/__init__.py`
- Empty file to mark `tests` as a Python package

**File:** `scripts/generate_input.py`
- Development helper script whose main purpose is to generate a sample input JSON file for the simulator
- Produces a file with 30 drivers and 70 rides for local testing
- This is a separate dev-time utility, not part of the main production runtime
- Use for fast local testing and to verify unmatched-ride behavior, with closely spaced timestamps to create rides that may remain unassigned

### 1.3 External Dependencies [DONE] ✓
- `pygeohash` - spatial neighbor geohash calculations
- `jsonschema` - input validation with JSON schemas

---

## Phase 2: Domain Entities (src/models.py)

**General Design Principles:**
- **Stateless Logic:** All helper functions and strategies are pure functions with no internal state. Calculations depend only on function parameters.
- **Single Source of Truth (Driver Availability):** A driver's availability is determined solely by its location in the data structures: presence in `spatial_index` means available, presence in `busy_drivers` heap means occupied.
- **Data Type Convention:** All times are stored as **float (Unix seconds)** internally for calculations. External JSON timestamps use ISO-8601 and are converted during parsing/serialization.

### 2.1 Location Class [DONE] ✓
**File:** `src/models.py`
**Class:** `Location`

**Implementation details:**
- Use `@dataclass(frozen=True)` so `__init__`, `__repr__`, `__eq__`, and `__hash__` are generated automatically.
- Keep the class immutable and hashable for use in sets and as dict keys.

**Fields:**
- `lat: float` - Latitude coordinate
- `lon: float` - Longitude coordinate

**Methods:**
- `distance_to(other: 'Location') -> float` - Calculate the great-circle distance in kilometers to another `Location` by delegating to the centralized `haversine()` function in `src/logic.py`.
  - Docstring note: Haversine distance approximates the straight-line great-circle distance on the Earth's surface and is the most accurate straight-line model for global coordinates.
- `to_geohash(precision: int = 6) -> str` - Convert the latitude/longitude pair to a geohash string using `pygeohash`.

**Dependencies:** `pygeohash`, `src.logic.haversine` (centralized geospatial calculation)

---

### 2.2 Driver Class [DONE] ✓
**File:** `src/models.py`
**Class:** `Driver`

**Fields:**
- `id: str` - Unique driver identifier
- `name: str` - Driver name
- `rating: float` - Driver rating (1-5 scale)
- `vehicle_type: str` - Type of vehicle (private, suv)
- `current_location: Location` - Current position (mutable)
- `available_at: float` - Unix timestamp (seconds) when driver becomes available

**Methods:**
- `__init__(id: str, name: str, rating: float, vehicle_type: str, location: Location)` - Constructor
- `update_location(new_location: Location) -> None` - Update driver's current location
- `__repr__() -> str` - String representation for debugging
- `__lt__(other: Driver) -> bool` - Less-than comparison for heap operations (by available_at)

**Note:** Driver availability is managed entirely by the Simulator: presence in `spatial_index` indicates availability, presence in `busy_drivers` heap indicates occupied status. No local state tracking required.

**Dependencies:** Location class

---

### 2.3 Ride Class [DONE] ✓
**File:** `src/models.py`
**Class:** `Ride`

**Fields:**
- `id: str` - Unique ride identifier
- `pickup: Location` - Pickup location
- `dropoff: Location` - Dropoff location
- `request_time_seconds: float` - Unix timestamp (seconds) used by the simulation engine
- `passenger_rating: float` - Passenger rating (1-5 scale)

**Methods:**
- `__init__(id: str, pickup: Location, dropoff: Location, request_time_seconds: float, passenger_rating: float)` - Constructor with validation
- `__post_init__()` - Validate numeric Unix-seconds timestamp
- `calculate_distance() -> float` - Get distance from pickup to dropoff in km using `pickup.distance_to(dropoff)` (which delegates to centralized `haversine()` function)
- `calculate_estimated_time(speed_kmh: float = BASE_SPEED_KMH) -> float` - Estimate trip duration in seconds
- `__repr__() -> str` - String representation for debugging

**Dependencies:** `Location` class, `timestamp_str_to_seconds()` from `src.logic`

---

## Phase 3: Mathematical & Geospatial Engine (src/logic.py) [DONE] ✓

**Module-Level Constants:**
- `GEOHASH_PRECISION: int = 5` - Geohash precision for spatial partitioning
- `BASE_SPEED_KMH: float = 30.0` - Default speed for travel time
- `MAX_PICKUP_DISTANCE_KM: float = 10.0` - Maximum allowed driver pickup distance
- `MAX_RATING_DIFF: float = 4.0` - Maximum rating difference between a 1-star and 5-star value
- `EARTH_RADIUS_KM: float = 6371` - Earth's mean radius in kilometers
- These constants are used across the system for travel estimation and normalized scoring logic.

**Global Time Conversion Functions:**
- `timestamp_str_to_seconds(timestamp_str: str) -> float` - Convert ISO-8601 string to Unix seconds using `datetime` module
- `seconds_to_timestamp_str(seconds: float) -> str` - Convert Unix seconds to ISO-8601 string
- `is_timed_out(request_time_seconds: float, current_time_seconds: float, timeout_seconds: float = 300) -> bool` - Check if ride exceeded timeout
- `format_duration(seconds: float) -> str` - Convert seconds to readable format (HH:MM:SS)

**Dependencies:** `datetime` module (standard library)

---

### 3.1 Geospatial Functions (Pure Functions)
**File:** `src/logic.py`

**Global Geospatial Functions:**
- `haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float` - Calculate great-circle distance between two coordinates in km using `math` module. This is the **centralized distance calculation** used by `Location.distance_to()` and `Ride.calculate_distance()`.
- `get_nearby_geohashes(geohash: str) -> List[str]` - Get neighboring geohash cells (9-cell neighborhood) using `pygeohash` library

**Dependencies:** `math` module (standard library), `pygeohash` library (3rd-party)

---

## Phase 4: Decision Logic (src/strategies/) [DONE] ✓

Implement strategies as a small package `src/strategies/` with three modules:

Files to create:
- `src/strategies/__init__.py` — simple package initializer exporting the strategy classes
- `src/strategies/base.py` — contains `BaseStrategy` (ABC)
- `src/strategies/shortest.py` — contains `ShortestDistanceStrategy`
- `src/strategies/weighted.py` — contains `WeightedScoreStrategy` (with private scoring helper)

### 4.1 `base.py` — BaseStrategy Abstract Class
**File:** `src/strategies/base.py`
**Class:** `BaseStrategy` (ABC - Abstract Base Class)

**Methods (abstract):**
- `match(ride: Ride, candidate_drivers: List[Driver]) -> Optional[Driver]` - Select a driver from candidates or return None

**Rationale:** Define contract for all strategy implementations

**Dependencies:** Location, Driver, Ride classes

---

### 4.2 `shortest.py` — ShortestDistanceStrategy
**File:** `src/strategies/shortest.py`
**Class:** `ShortestDistanceStrategy(BaseStrategy)`

**Methods:**
- `match(ride: Ride, candidate_drivers: List[Driver]) -> Optional[Driver]` - Return driver with minimum haversine distance to pickup location
  - Return None if candidates list is empty
  - Use `Location.haversine_distance_to()` to compute distances

**Dependencies:** `BaseStrategy`, `Location`, `Driver`, `Ride`

---

### 4.3 `weighted.py` — WeightedScoreStrategy
**File:** `src/strategies/weighted.py`
**Class:** `WeightedScoreStrategy(BaseStrategy)`

**Module Contents:**

#### 4.3.1 ScoringEngine Utility Class
**Class:** `ScoringEngine`

**Constants:**
- `WEIGHT_DISTANCE: float = 0.3` - Weight for normalized distance component (w1)
- `WEIGHT_RATING: float = 0.7` - Weight for normalized rating difference component (w2)

**Methods (static):**
- `compare_scores(score1: float, score2: float) -> int` - Return -1, 0, or 1 for sorting

#### 4.3.2 WeightedScoreStrategy Class
**Class:** `WeightedScoreStrategy(BaseStrategy)`

**Notes:**
- The weighted-score calculation is specific to this strategy and implemented as a private method `_calculate_weighted_score(...)`.
- Weight constants and comparison logic are scoped within this module via `ScoringEngine`.
- Documentation in `src/logic.py` should explain that the goal is "Symmetric Quality Matching": matching drivers and passengers by both distance and rating compatibility.
- Using global constants for normalization allows future tuning of pickup radius and score weights without changing the function logic itself.

**Methods:**
- `match(ride: Ride, candidate_drivers: List[Driver]) -> Optional[Driver]` - Return driver with lowest weighted score
  - For each candidate: score = `_calculate_weighted_score(distance, driver_rating, passenger_rating)`
  - Use `ScoringEngine.compare_scores()` to find minimum score
  - Return None if candidates list is empty
  - Return driver with minimum score
  - Documentation refined to clarify that lower score indicates a better weighted match

**Private Methods:**
- `_calculate_weighted_score(distance: float, driver_rating: float, passenger_rating: float) -> float` - Compute weighted score using ScoringEngine weights
  - Normalized distance: `d_norm = min(distance / MAX_PICKUP_DISTANCE_KM, 1.0)`
  - Normalized rating difference: `r_norm = abs(driver_rating - passenger_rating) / MAX_RATING_DIFF`
  - Formula: `score = (w1 * d_norm) + (w2 * r_norm)`
  - Lower score is better: short normalized distance and small normalized rating mismatch produce the strongest matches

**Dependencies:** `BaseStrategy`, `Location`, `Driver`, `Ride`, `ScoringEngine`

---

## Phase 5: Simulation Orchestration (src/simulator.py) [DONE] ✓

### 5.1 Simulator Class
**File:** `src/simulator.py`
**Class:** `Simulator`

**Fields:**
- `strategy: BaseStrategy` - Matching strategy instance
- `spatial_index: Dict[str, List[Driver]]` - Geohash -> List of available drivers
- `busy_drivers: List[Driver]` - Min-heap of busy drivers sorted by available_at
- `pending_rides: deque[Ride]` - Queue of unmatched rides
- `current_time: float` - Current simulation time (Unix seconds)
- `assignments: List[Dict]` - List of successful matches
- `unassigned: List[str]` - List of unmatched ride IDs
- `metrics: Dict` - Performance metrics (average wait time, driver stats)

**Methods:**

#### 5.1.1 Constructor
- `__init__(strategy: BaseStrategy)` - Initialize simulator with strategy
  - Initialize current_time to `None` or `0` as placeholder
  - Initialize empty spatial_index, busy_drivers heap, pending_rides deque
  - Initialize empty assignments, unassigned, metrics
  - Note: actual simulation start time is set once inside `run()` from the first sorted ride request time

#### 5.1.2 State Management
- `add_driver(driver: Driver) -> None` - Add driver to spatial index
  - Calculate geohash from driver location
  - Add to spatial_index[geohash] list

- `add_ride_to_queue(ride: Ride) -> None` - Add ride to pending queue
  - Append to pending_rides

- `release_available_drivers(current_time: float) -> None` - Move completed drivers from `busy_drivers` heap back into `spatial_index` dict once their `available_at` time has arrived
  - The Simulator is responsible for the physical movement of driver objects between busy and available state via these data structures
  - While busy_drivers not empty AND top driver's available_at <= current_time:
    - Pop driver from heap
    - Update driver.current_location to trip dropoff
    - Add driver back to spatial_index

#### 5.1.3 Spatial Filtering & Constraints
- `get_candidate_drivers(ride: Ride) -> List[Driver]` - Find available drivers near pickup location
  - Calculate pickup geohash using precision `GEOHASH_PRECISION` (global constant = 5)
  - Search only the 9-cell neighborhood: current geohash plus its 8 adjacent neighbors via `get_nearby_geohashes()`
  - Collect all available drivers from spatial_index for those 9 geohashes
  - Filter 1: only include drivers whose `vehicle_type` matches ride requirements
  - Filter 2: only include drivers whose distance to pickup is <= `MAX_PICKUP_DISTANCE_KM`
  - If no candidates remain after these filters, do not search all drivers; instead leave the ride in `pending_rides`
  - Return list of candidates

#### 5.1.4 Matching & Assignment
- `match_ride(ride: Ride) -> Optional[Driver]` - Attempt to match ride using strategy
  - Get candidates via get_candidate_drivers()
  - Call strategy.match(ride, candidates)
  - Return matched driver or None

- `assign_ride(ride: Ride, driver: Driver) -> None` - Execute ride assignment
  - Add to assignments list with: {timestamp, ride_id, driver_id}
  - Remove driver from spatial_index
  - Calculate driver travel time to pickup:
    - `pickup_distance_km = driver.current_location.haversine_distance_to(ride.pickup)`
    - `pickup_travel_seconds = (pickup_distance_km / BASE_SPEED_KMH) * 3600`
  - Calculate ride trip duration:
    - `trip_distance_km = ride.calculate_distance()`
    - `trip_duration_seconds = (trip_distance_km / BASE_SPEED_KMH) * 3600`
  - Set driver.available_at = `current_time + pickup_travel_seconds + trip_duration_seconds`
  - Record `pickup_travel_seconds` for metrics as driver arrival delay
  - Update metrics for this assignment (global and per-driver stats)
  - Add driver to busy_drivers heap

#### 5.1.5 Main Execution Loop
- `run(rides: List[Ride]) -> Dict` - Execute simulation using a discrete-event event-driven loop
  - Assumes `rides` has been sorted in `main()` in-place deterministically by: `(request_time_seconds, distance, ride_id)`
  - Initialize `current_time` to `rides[0].request_time_seconds` if rides exist
  - Maintain:
    - `pending_rides`: queue of rides waiting for a driver
    - `unassigned`: list of rides that timed out (>300 seconds wait) or remained unmatched after simulation end
    - `assignments`: list of successful ride-driver matches
  - While there are rides left in `rides` not yet processed OR there are rides in `pending_rides` that have not yet timed out:
    - Determine the next event time:
      - `next_ride_arrival_time` = next ride request time from sorted_rides, or `inf` if none remain
      - `next_driver_release_time` = `available_at` of the heap root in `busy_drivers`, or `inf` if none are busy
      - `next_event_time` = min(`next_ride_arrival_time`, `next_driver_release_time`)
    - Update `current_time` to `next_event_time` (never move time backwards)
    - Maintenance:
      - Release drivers: pop all drivers from `busy_drivers` whose `available_at <= current_time` and add them back into `spatial_index`
    - Process pending rides:
      - Attempt to match pending rides against currently available drivers using the chosen strategy
      - For each matched pending ride, add assignment to `assignments` and remove it from `pending_rides`
    - Timeout pending rides: remove any `pending_rides` whose wait time exceeds 300 seconds and append them to `unassigned`
    - Handle new arrival if `next_event_time` equals `next_ride_arrival_time`:
      - Pop the next ride from `sorted_rides`
      - Attempt immediate matching
      - If matched: add to `assignments`
      - If not matched: append to `pending_rides`
  - After the loop ends, move any remaining `pending_rides` into `unassigned`
  - Return `{assignments, unassigned, metrics}`

#### 5.1.6 Metrics Calculation
- `calculate_metrics() -> Dict` - Compute performance statistics
  - global_average_arrival_time: mean time from request to assignment of all assigned rides (in minutes)
  - driver_stats: Dict per driver_id with {ride_count, average_arrival_time (minutes)}

**Dependencies:** BaseStrategy, Driver, Ride, global time/geo functions

---

## Phase 6: Data Input/Output (src/parser.py) [DONE] ✓

**Input Format:**
- Single JSON file containing both drivers and rides: `{"drivers": [...], "rides": [...]}`
- Parser validates input using JSON Schema; invalid records are skipped with warning logs

### 6.1 JSON Schema Validation
**File:** `src/parser.py`

**Validation Strategy:**
- Define two JSON schemas (one for drivers, one for rides) that enforce:
  - Required fields: all required fields must be present
  - Type constraints: strings, floats, etc.
  - Range constraints: latitude [-90, 90], longitude [-180, 180], ratings [1, 5], request_time in ISO-8601 format
- Use `jsonschema` library to validate each record
- If validation fails, log warning, skip record, continue to next

**Dependencies:** `jsonschema` library (3rd-party)

---

### 6.2 Parser Functions
**File:** `src/parser.py`

#### 6.2.1 JSON Parsing with Schema Validation
- `parse_input_json(filepath: str) -> Tuple[List[Driver], List[Ride]]` - Load and validate drivers and rides from one JSON file
  - Read JSON file with structure: `{"drivers": [...], "rides": [...]}`
  - For each driver record:
    - Validate against driver schema
    - If valid: convert to Driver object, add to drivers list
    - If invalid: log warning, skip record
  - For each ride record:
    - Validate against ride schema
    - If valid: convert `request_time` (ISO-8601) to float seconds, create Ride object, add to rides list
    - If invalid: log warning, skip record
  - Return tuple: (drivers, rides)

**Dependencies:** Location, Driver, Ride, global time conversion functions, `jsonschema` library

---

### 6.3 OutputReporter Functions
**File:** `src/parser.py`

**Functions:**

#### 6.3.1 Report Generation
- `generate_report(simulator_results: Dict) -> Dict` - Format simulation results for output
  - Receive assignments, unassigned, and precomputed metrics from simulator results
  - Create structured report with:
    - assignments: List of {timestamp, ride_id, driver_id}
    - unassigned: List of ride_ids (timed out or never matched)
    - metrics:
      - global_average_arrival_time: mean arrival time to pickup (from request to assignment) across all assigned rides (in minutes, round 2 digits)
      - total_assigned: count of assigned rides
      - total_unassigned: count of unassigned rides
      - driver_stats: List of {driver_id, name, ride_count, average_arrival_time}
  - Return report dict

#### 6.3.2 Output Serialization
- `save_to_json(report: Dict, output_filepath: str) -> None` - Write report to JSON file
  - Serialize report dict to JSON with indentation
  - Save to output_filepath
  - JSON structure:
    ```json
    {
      "assignments": [{"timestamp": "2024-05-19T10:30:00Z", "ride_id": "...", "driver_id": "..."}, ...],
      "unassigned": ["ride_id1", "ride_id2", ...],
      "metrics": {
        "global_average_arrival_time": 123.45,
        "total_assigned": 100,
        "total_unassigned": 5,
        "driver_stats": [{"driver_id": "d1", "ride_count": 3, "average_arrival_time": 120.5}, ...]
      }
    }
    ```

**Dependencies:** json module, Simulator

---

## Phase 7: Main Entry Point (main.py) [DONE] ✓

### 7.1 Main Function
**File:** `main.py` (at project root)

**Function:** `main() -> int`

**CLI Arguments:**
- `--input` (optional, default='data/input.json'): Path to input JSON file (contains drivers and/or rides)
- `--strategy` (optional, default='weighted'): 'shortest' or 'weighted'
- `--output` (optional, default='output/results.json'): Output JSON path
- `--dev` (optional, flag): Enable DEV mode (logs printed to console + logs folder; without flag, only logs folder)

**Logic:**
- Create `logs/` directory if it does not exist
- Setup logging: use `logging.basicConfig()` in `main.py` to configure a timestamped log file in `logs/` and optional console output when `--dev` is set
  - Log file name format: `simulation_YYYY-MM-DD_HH-MM-SS.log`
  - INFO: Ride matched/unmatched events
  - WARNING: Invalid records skipped during input parsing
  - ERROR: Critical failures (file not found, invalid JSON, etc.)
- Parse command-line arguments
- Load input JSON file via `InputParser.parse_input_json(input_path)`
  - The parser handles one JSON input file containing both drivers and rides
  - The main program expects this input file to already exist; it does not generate the input itself
  - Handle missing input file and invalid JSON with logged error messages
- Validate strategy name; exit with help message if invalid
- Instantiate strategy based on --strategy argument
- Sort `rides` in-place deterministically by `(request_time_seconds, distance (of the ride), ride_id)`
- Create Simulator(strategy)
- For each driver: simulator.add_driver()
- Call simulator.run(rides) -> results
- Call OutputReporter.generate_report(results) -> report
- Call OutputReporter.save_to_json(report, output_path)
  - Handle file write errors with a logged message and optional fallback behavior
- Log all details to logs/ folder
- Return 0 on success, non-zero on error

**Dependencies:** argparse, sys, logging, os, glob, and all src modules

---

## Phase 8: Unit Tests (tests/)

### 8.1 Test Files Structure
- `tests/test_models.py` - Test Location, Driver, Ride classes
- `tests/test_logic.py` - Test time/geo functions
- `tests/test_strategies.py` - Test strategy implementations (BaseStrategy, ShortestDistanceStrategy, WeightedScoreStrategy, ScoringEngine)
- `tests/test_simulator.py` - Test Simulator orchestration
- `tests/test_parser.py` - Test JSON parsing and validation
- `tests/test_integration.py` - End-to-end simulation tests

**Testing Framework:** pytest

---

## Phase 9: README Documentation

### 9.1 README Content
- `README.md` will explain the project purpose, usage, architecture, and assumptions.
- Include a quick start section with commands for installing dependencies, running the simulator, and running tests.
- Describe the input JSON format and output report structure.
- Document the available strategy options (`shortest`, `weighted`) and how to select them via CLI.
- Explain logging behavior and the purpose of `--dev` mode.

### 9.2 Implementation Assumptions
- The simulator uses discrete-event simulation: time advances only to the next ride arrival or driver release event.
- All times are represented internally as Unix seconds; external JSON uses ISO-8601 timestamps.
- Rides are sorted deterministically by `(request_time_seconds, distance, ride_id)` before simulation:
  - `request_time_seconds` ensures rides are processed in chronological order,
  - `distance` prioritizes shorter trips first to improve system responsiveness and customer experience by freeing drivers earlier,
  - `ride_id` makes the ordering deterministic when times and distances are equal.
- A driver is considered available if present in the spatial index; otherwise the driver is busy and stored in a heap by `available_at`.
- Pickup distance is constrained by `MAX_PICKUP_DISTANCE_KM`, and only drivers within the 9-cell geohash neighborhood are considered.
- Weighted matching uses `distance_weight=0.3` and `rating_weight=0.7` and normalizes distance/rating difference for comparability.
- The input JSON contains both `drivers` and `rides` in a single file; invalid records are skipped with warnings.
- The system reports unassigned rides when they time out after 300 seconds (5 minutes) or remain unmatched at simulation end.

### 9.3 README Structure
- Project overview
- Installation and dependencies
- CLI usage examples
- Input/output format
- Strategy descriptions
- Assumptions and design decisions
- Testing instructions
- Logging and output details

---

## Execution Order

**Build sequence (numerically deterministic):**

1. Phase 1: Create directory structure
2. Phase 2: Implement all classes in src/models.py
3. Phase 3: Implement all utilities in src/logic.py
4. Phase 4: Implement all strategies in src/strategies/
5. Phase 5: Implement Simulator in src/simulator.py
6. Phase 6: Implement I/O handlers in src/parser.py
7. Phase 7: Implement main.py entry point
8. Phase 8: Write comprehensive test suite
