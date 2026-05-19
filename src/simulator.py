"""Simulator orchestration for the Ride Share Simulator.

Implements a discrete-event simulator that assigns drivers to rides
using a pluggable `BaseStrategy` implementation.
"""
from collections import deque, defaultdict
from typing import Dict, List, Optional
import heapq
import logging

from src.logic import (
    GEOHASH_PRECISION,
    BASE_SPEED_KMH,
    MAX_PICKUP_DISTANCE_KM,
    RIDE_REQUEST_TIMEOUT_SECONDS,
    get_nearby_geohashes,
)
from src.models import Driver, Ride
from src.strategies.base import BaseStrategy


logger = logging.getLogger(__name__)


class Simulator:
    """Discrete-event simulator that assigns drivers to rides.

    The simulator advances time only to the next ride arrival or the next
    driver release event. Drivers are stored in a geohash-based spatial index
    while available and in a min-heap (`busy_drivers`) while servicing rides.
    """

    def __init__(self, strategy: BaseStrategy):
        self.strategy = strategy
        self.spatial_index: Dict[str, List[Driver]] = defaultdict(list)
        self.busy_drivers: List[Driver] = []  # heap by available_at via Driver.__lt__
        self.pending_rides: deque[Ride] = deque()
        self.current_time: float = 0.0

        self.assignments: List[Dict] = []
        self.unassigned: List[str] = []
        self.metrics: Dict = {
            "pickup_travel_minutes": [],
            "driver_stats": defaultdict(list),
        }

    # --- State management -------------------------------------------------
    def add_driver(self, driver: Driver) -> None:
        """Add a driver to the spatial index (mark as available)."""
        gh = driver.current_location.to_geohash(GEOHASH_PRECISION)
        self.spatial_index[gh].append(driver)
        logger.debug("Added driver %s to spatial_index at geohash %s", driver.id, gh)

    def add_ride_to_queue(self, ride: Ride) -> None:
        """Append a ride to the pending queue."""
        self.pending_rides.append(ride)
        logger.debug("Queued ride %s (request_time=%s)", ride.id, getattr(ride, 'request_time_str', ''))

    def release_available_drivers(self, current_time: float) -> None:
        """Move drivers whose `available_at` <= current_time back into spatial_index."""
        while self.busy_drivers and self.busy_drivers[0].available_at <= current_time:
            driver = heapq.heappop(self.busy_drivers)
            # driver.current_location is expected to be updated to dropoff at assignment
            gh = driver.current_location.to_geohash(GEOHASH_PRECISION)
            self.spatial_index[gh].append(driver)
            logger.debug("Released driver %s back to spatial_index at geohash %s (available_at=%.1f)", driver.id, gh, driver.available_at)

    # --- Candidate selection ----------------------------------------------
    def get_candidate_drivers(self, ride: Ride) -> List[Driver]:
        """Return available drivers near `ride.pickup` within MAX_PICKUP_DISTANCE_KM."""
        pickup_gh = ride.pickup.to_geohash(GEOHASH_PRECISION)
        neighborhood = get_nearby_geohashes(pickup_gh)

        # Ride requirement: `vehicle_type` ('suv' or 'private') must match driver
        required_vehicle = ride.vehicle_type

        candidates: List[Driver] = []
        for gh in neighborhood:
            for driver in list(self.spatial_index.get(gh, [])):
                # Enforce vehicle type match
                if driver.vehicle_type != required_vehicle:
                    continue

                dist = driver.current_location.distance_to(ride.pickup)
                if dist <= MAX_PICKUP_DISTANCE_KM:
                    candidates.append(driver)

        logger.debug(
            "Found %d candidate drivers near geohash %s (required_vehicle=%s)",
            len(candidates),
            pickup_gh,
            required_vehicle,
        )

        return candidates

    # --- Matching & assignment --------------------------------------------
    def match_ride(self, ride: Ride) -> Optional[Driver]:
        candidates = self.get_candidate_drivers(ride)
        return self.strategy.match(ride, candidates)

    def assign_ride(self, ride: Ride, driver: Driver) -> None:
        """Perform assignment bookkeeping and move driver to busy heap."""
        self.assignments.append({"timestamp": self.current_time, "ride_id": ride.id, "driver_id": driver.id})
        logger.info("Assigned ride %s to driver %s at %.1f", ride.id, driver.id, self.current_time)

        # Remove driver from spatial_index
        gh = driver.current_location.to_geohash(GEOHASH_PRECISION)
        if driver in self.spatial_index.get(gh, []):
            self.spatial_index[gh].remove(driver)

        # Travel times
        pickup_distance_km = driver.current_location.distance_to(ride.pickup)
        pickup_travel_seconds = (pickup_distance_km / BASE_SPEED_KMH) * 3600.0
        pickup_travel_minutes = pickup_travel_seconds / 60.0
        trip_duration_seconds = ride.calculate_estimated_time(BASE_SPEED_KMH)

        # Set driver available_at and update location to dropoff (simulated arrival)
        driver.available_at = self.current_time + pickup_travel_seconds + trip_duration_seconds
        driver.current_location = ride.dropoff

        # Record metrics (store minutes)
        self.metrics["pickup_travel_minutes"].append(pickup_travel_minutes)
        self.metrics["driver_stats"][driver.id].append(pickup_travel_minutes)
        logger.debug("Pickup travel: ride=%s driver=%s minutes=%.2f", ride.id, driver.id, pickup_travel_minutes)

        # Add to busy heap
        heapq.heappush(self.busy_drivers, driver)

    # --- Main loop -------------------------------------------------------
    def run(self, rides: List[Ride]) -> Dict:
        """Run the discrete-event simulation over provided `rides`.

        Rides are expected to arrive already sorted by request_time_seconds before processing.
        Returns a dict with `assignments`, `unassigned`, and `metrics`.
        """
        if not rides:
            logger.info("No rides to simulate.")
            return {"assignments": [], "unassigned": [], "metrics": {}}

        ride_idx = 0
        self.current_time = rides[0].request_time_seconds
        logger.info("Starting simulation: %d rides", len(rides))

        while ride_idx < len(rides) or self.pending_rides:
            # Determine next event times
            next_ride_time = rides[ride_idx].request_time_seconds if ride_idx < len(rides) else float("inf")
            next_driver_release = self.busy_drivers[0].available_at if self.busy_drivers else float("inf")
            next_event_time = min(next_ride_time, next_driver_release)

            # Advance time
            self.current_time = max(self.current_time, next_event_time)

            # Release drivers that have completed trips
            self.release_available_drivers(self.current_time)

            # Process pending rides first
            pending_len = len(self.pending_rides)
            for _ in range(pending_len):
                pending = self.pending_rides.popleft()
                driver = self.match_ride(pending)
                if driver:
                    self.assign_ride(pending, driver)
                else:
                    # Check timeout
                    if (self.current_time - pending.request_time_seconds) > RIDE_REQUEST_TIMEOUT_SECONDS:
                        self.unassigned.append(pending.id)
                    else:
                        self.pending_rides.append(pending)

            # Handle next arriving ride
            if next_event_time == next_ride_time and ride_idx < len(rides):
                ride = rides[ride_idx]
                ride_idx += 1
                driver = self.match_ride(ride)
                if driver:
                    self.assign_ride(ride, driver)
                else:
                    self.pending_rides.append(ride)

            # If no events left, break
            if next_event_time == float("inf"):
                break

        # Move remaining pending rides to unassigned
        while self.pending_rides:
            r = self.pending_rides.popleft()
            self.unassigned.append(r.id)
        results = {"assignments": self.assignments, "unassigned": self.unassigned, "metrics": self.calculate_metrics()}
        logger.info("Simulation finished: %d assigned, %d unassigned", len(self.assignments), len(self.unassigned))
        return results

    def calculate_metrics(self) -> Dict:
        """Compute summary metrics from recorded data."""
        pickup_list = self.metrics.get("pickup_travel_minutes", [])
        total_assigned = len(self.assignments)
        # pickup_list already in minutes
        global_avg = round((sum(pickup_list) / len(pickup_list)), 2) if pickup_list else 0.0

        driver_stats = []
        for driver_id, times in self.metrics.get("driver_stats", {}).items():
            # times are stored in minutes
            avg = round((sum(times) / len(times)), 2) if times else 0.0
            driver_stats.append({"driver_id": driver_id, "ride_count": len(times), "average_arrival_time": avg})

        return {"global_average_arrival_time": global_avg, "total_assigned": total_assigned, "total_unassigned": len(self.unassigned), "driver_stats": driver_stats}
