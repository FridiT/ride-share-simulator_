"""Shortest distance matching strategy for ride-share assignments."""

from typing import List, Optional

from src.models import Driver, Ride
from src.strategies.base import BaseStrategy


class ShortestDistanceStrategy(BaseStrategy):
    """Strategy that matches rides to the geographically closest available driver.
    
    This strategy prioritizes proximity, selecting the driver with the minimum
    haversine distance to the ride's pickup location.
    """

    def match(self, ride: Ride, candidate_drivers: List[Driver]) -> Optional[Driver]:
        """Return the driver with minimum distance to the pickup location.
        
        Args:
            ride: The ride request to match.
            candidate_drivers: List of available drivers to consider.
            
        Returns:
            The driver closest to the pickup location, or None if no candidates.
        """
        if not candidate_drivers:
            return None

        # Find the driver with minimum distance to the pickup location
        closest_driver = min(
            candidate_drivers,
            key=lambda driver: driver.current_location.distance_to(ride.pickup)
        )
        return closest_driver
