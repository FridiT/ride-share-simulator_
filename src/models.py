from dataclasses import dataclass, field
import math

import pygeohash

from src.logic import BASE_SPEED_KMH, haversine


@dataclass(frozen=True)
class Location:
    """Immutable geographic point represented by latitude and longitude."""

    lat: float
    lon: float

    def distance_to(self, other: "Location") -> float:
        """Return the great-circle Haversine distance in kilometers to another Location.

        Delegates to the haversine function in logic module for the calculation.
        """
        return haversine(self.lat, self.lon, other.lat, other.lon)

    def to_geohash(self, precision: int = 6) -> str:
        """Convert the location to a geohash string at the requested precision.
        precision: The number of characters in the resulting geohash string.
        A higher value increases accuracy but creates smaller grid cells.
        For city-scale ride-sharing (10km radius), precision 6 is recommended
        """
        if precision <= 0:
            raise ValueError("Geohash precision must be a positive integer.")

        return pygeohash.encode(self.lat, self.lon, precision=precision)


@dataclass
class Driver:
    """Represents a ride-share driver with mutable location tracking.
    
    The driver's availability is managed externally by the Simulator:
    presence in available_drivers_by_geohash indicates availability, while presence
    in busy_drivers heap indicates the driver is currently on a ride.
    """

    id: str
    name: str
    rating: float
    vehicle_type: str
    current_location: Location
    available_at: float = field(default=0.0)

    def __post_init__(self) -> None:
        """Validate driver fields upon creation."""
        if not self.id:
            raise ValueError("Driver id cannot be empty.")
        if not self.name:
            raise ValueError("Driver name cannot be empty.")
        if not 1.0 <= self.rating <= 5.0:
            raise ValueError("Driver rating must be between 1.0 and 5.0.")
        if not self.vehicle_type:
            raise ValueError("Driver vehicle_type cannot be empty.")
        if self.available_at < 0.0:
            raise ValueError("Driver available_at cannot be negative.")

    def update_location(self, new_location: Location) -> None:
        """Update the driver's current location."""
        self.current_location = new_location

    def __lt__(self, other: "Driver") -> bool:
        """Compare drivers by available_at for heap operations."""
        return self.available_at < other.available_at

    def __repr__(self) -> str:
        """Return a readable representation of the driver."""
        return (
            f"Driver(id={self.id!r}, name={self.name!r}, rating={self.rating}, "
            f"vehicle_type={self.vehicle_type!r}, "
            f"current_location={self.current_location}, available_at={self.available_at})"
        )


@dataclass
class Ride:
    """Represents a passenger ride request with pickup/dropoff locations and ratings.
    
    The request_time_seconds field is the request timestamp in Unix seconds.
    """

    id: str
    pickup: Location
    dropoff: Location
    request_time_seconds: float
    passenger_rating: float
    vehicle_type: str = "private"

    def __post_init__(self) -> None:
        """Validate ride fields and numeric request timestamp."""
        if not self.id:
            raise ValueError("Ride id cannot be empty.")
        if not 1.0 <= self.passenger_rating <= 5.0:
            raise ValueError("Passenger rating must be between 1.0 and 5.0.")

        if self.vehicle_type not in ("private", "suv"):
            raise ValueError("vehicle_type must be one of: 'private', 'suv'.")

        if not isinstance(self.request_time_seconds, (int, float)) or isinstance(self.request_time_seconds, bool):
            raise ValueError("Ride request_time_seconds must be a numeric timestamp.")
        if self.request_time_seconds < 0.0 or math.isnan(self.request_time_seconds) or math.isinf(self.request_time_seconds):
            raise ValueError("Ride request_time_seconds must be a non-negative finite timestamp.")

    def calculate_distance(self) -> float:
        """Calculate the distance from pickup to dropoff in kilometers.
        
        Returns:
            Distance in kilometers using Haversine formula.
        """
        return self.pickup.distance_to(self.dropoff)

    def calculate_estimated_time(self, speed_kmh: float = BASE_SPEED_KMH) -> float:
        """Estimate the trip duration in seconds.
        
        Args:
            speed_kmh: Average travel speed in km/h (default uses BASE_SPEED_KMH).
            
        Returns:
            Estimated trip duration in seconds.
            
        Raises:
            ValueError: If speed_kmh is not positive.
        """
        if speed_kmh <= 0:
            raise ValueError("Speed must be positive.")

        distance_km = self.calculate_distance()
        hours = distance_km / speed_kmh
        return hours * 3600.0

    def __repr__(self) -> str:
        """Return a readable representation of the ride."""
        return (
            f"Ride(id={self.id!r}, pickup={self.pickup}, dropoff={self.dropoff}, "
            f"request_time_seconds={self.request_time_seconds}, passenger_rating={self.passenger_rating})"
        )
