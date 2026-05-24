"""Abstract base class for ride-driver matching strategies."""

from abc import ABC, abstractmethod
from typing import List, Optional

from src.models import Driver, Ride


class BaseStrategy(ABC):
    """Abstract base class defining the contract for matching strategies.
    
    All strategy implementations must provide a match() method that selects
    a driver from a list of candidates to be assigned to a ride.
    """

    @abstractmethod
    def match(self, ride: Ride, candidate_drivers: List[Driver]) -> Optional[Driver]:
        """Select a driver from candidates to match with a ride.
        
        Args:
            ride: The ride request to match.
            candidate_drivers: List of available drivers near the pickup location.
            
        Returns:
            A Driver object if a match is found, None otherwise.
        """
        pass
