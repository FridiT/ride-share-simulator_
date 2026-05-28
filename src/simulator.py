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
    is_timed_out,
    seconds_to_timestamp_str,
    get_nearby_geohashes,
)
from src.logic import RIDE_REQUEST_TIMEOUT_SECONDS
from src.models import Driver, Ride
from src.strategies.base import BaseStrategy


logger = logging.getLogger(__name__)


class Simulator:
    """Discrete-event simulator that assigns drivers to rides.

    The simulator advances time only to the next ride arrival or the next
    driver release event. Drivers are stored in a geohash-based availability index
    while available and in a min-heap (`busy_drivers`) while servicing rides.
    """

    def __init__(self, strategy: BaseStrategy):
        self.strategy = strategy
        self.available_drivers_by_geohash: Dict[str, List[Driver]] = defaultdict(list)
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
        """Add a driver to the availability index (mark as available)."""
        geohash_key = driver.current_location.to_geohash(GEOHASH_PRECISION)
        self.available_drivers_by_geohash[geohash_key].append(driver)
        logger.debug("Added driver %s to availability index at geohash %s", driver.id, geohash_key)

    def add_ride_to_queue(self, ride: Ride) -> None:
        """Append a ride to the pending queue."""
        self.pending_rides.append(ride)
        logger.debug("Queued ride %s (request_time=%s)", ride.id, getattr(ride, 'request_time_str', ''))

    def release_available_drivers(self, current_time: float) -> None:
        """Move drivers whose `available_at` <= current_time back into availability index."""
        while self.busy_drivers and self.busy_drivers[0].available_at <= current_time:
            driver = heapq.heappop(self.busy_drivers)
            # driver.current_location is expected to be updated to dropoff at assignment
            geohash_key = driver.current_location.to_geohash(GEOHASH_PRECISION)
            self.available_drivers_by_geohash[geohash_key].append(driver)
            logger.debug("Released driver %s back to availability index at geohash %s (available_at=%.1f)", driver.id, geohash_key, driver.available_at)

    # --- Candidate selection ----------------------------------------------
    def get_candidate_drivers(self, ride: Ride) -> List[Driver]:
        """Return available drivers near `ride.pickup` within MAX_PICKUP_DISTANCE_KM."""
        pickup_gh = ride.pickup.to_geohash(GEOHASH_PRECISION)
        neighborhood = get_nearby_geohashes(pickup_gh)

        # Ride requirement: `vehicle_type` ('suv' or 'private') must match driver
        required_vehicle = ride.vehicle_type

        candidates: List[Driver] = []
        for geohash_key in neighborhood:
            for driver in list(self.available_drivers_by_geohash.get(geohash_key, [])):
                # Enforce vehicle type match
                if driver.vehicle_type != required_vehicle:
                    continue

                # todo: this note is relevant just for a new feature that soppurts preorder rides
                # add condition that check the driver duration to the pickup be less then the required time - (.....)
                # if ride.request_time_seconds < driver.available_at + ride.(duration....from driver.location to ride.pickup):
                #     continue

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
        # todo: we could to put the match in different module and make it more generic, so we can use it for different types of matching (e.g. matching passengers to drivers, matching drivers to passengers, etc.). 
        # This way we can have a more flexible and extensible design that can accommodate different use cases and requirements.
        candidates = self.get_candidate_drivers(ride)
        return self.strategy.match(ride, candidates)

    def assign_ride(self, ride: Ride, driver: Driver) -> None:
        """Perform assignment bookkeeping and move driver to busy heap."""
        external_timestamp = seconds_to_timestamp_str(self.current_time)
        self.assignments.append({"timestamp": external_timestamp, "ride_id": ride.id, "driver_id": driver.id})
        logger.info("Assigned ride %s to driver %s at timestamp %s", ride.id, driver.id, external_timestamp)

        # Remove driver from availability index
        geohash_key = driver.current_location.to_geohash(GEOHASH_PRECISION)
        if driver in self.available_drivers_by_geohash.get(geohash_key, []):
            self.available_drivers_by_geohash[geohash_key].remove(driver)

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

            # todo: this if is new part, for a case without a new ride arrival or driver release, but with pending rides in the queue
            
            # If there are no future ride arrivals or driver releases, but
            # there are pending rides, advance time only to the point where
            # pending rides would expire instead of setting time to inf.
            if next_event_time == float("inf") and self.pending_rides:
                expire_time = max(
                    (p.request_time_seconds + RIDE_REQUEST_TIMEOUT_SECONDS) for p in self.pending_rides
                )
                # Advance slightly past the exact expiry so `is_timed_out` (which uses
                # a strict > comparison) evaluates True and pending rides are handled
                # instead of repeatedly re-queuing at the same timestamp.
                next_event_time = expire_time + 1.0

            # Advance time (safe finite value)
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
                    if is_timed_out(pending.request_time_seconds, self.current_time):
                        logger.info(
                            "Unassigned ride %s after timeout at simulation time %s",
                            pending.id,
                            seconds_to_timestamp_str(self.current_time),
                        )
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
                    logger.debug(
                        "Queued arriving ride %s at %s (pending_queue_size=%d)",
                        ride.id,
                        seconds_to_timestamp_str(self.current_time),
                        len(self.pending_rides),
                    )

            # If no events left, break # TODO: should be in the beginning of the function
            if next_event_time == float("inf"):
                break

        # Move remaining pending rides to unassigned
        while self.pending_rides:
            pending_ride = self.pending_rides.popleft()
            logger.info(
                "Unassigned ride %s at end of simulation (no assignment found)",
                pending_ride.id,
            )
            self.unassigned.append(pending_ride.id)
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
