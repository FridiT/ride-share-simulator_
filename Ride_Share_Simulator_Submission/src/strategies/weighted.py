"""Weighted score matching strategy combining distance and rating compatibility."""

from typing import List, Optional

from src.logic import MAX_PICKUP_DISTANCE_KM, MAX_RATING_DIFF
from src.models import Driver, Ride
from src.strategies.base import BaseStrategy


class ScoringEngine:
    """Utility class for scoring driver-ride pairs with weighted criteria.
    
    This engine combines normalized distance and rating difference to produce
    a composite score. Lower scores indicate better matches.
    """

    # Weight constants for composite score calculation
    WEIGHT_DISTANCE: float = 0.3  # Weight for normalized distance component
    WEIGHT_RATING: float = 0.7    # Weight for normalized rating difference component

    @staticmethod
    def compare_scores(score1: float, score2: float) -> int:
        """Compare two scores for sorting.
        
        Args:
            score1: First score value.
            score2: Second score value.
            
        Returns:
            int: Comparison result for sorting helpers.
                Lower scores represent better weighted matches.
        """
        if score1 < score2:
            return -1
        elif score1 > score2:
            return 1
        else:
            return 0


class WeightedScoreStrategy(BaseStrategy):
    """Strategy that matches rides using a weighted combination of distance and rating.
    
    Implements "Symmetric Quality Matching" by scoring each driver based on both
    proximity (distance to pickup) and compatibility (rating similarity with passenger).
    Lower scores represent better matches.
    
    Scoring formula:
        score = (w1 * d_norm) + (w2 * r_norm)
        where:
        - d_norm = min(distance / MAX_PICKUP_DISTANCE_KM, 1.0)
        - r_norm = abs(driver_rating - passenger_rating) / MAX_RATING_DIFF
        - w1 = 0.3 (distance weight), w2 = 0.7 (rating weight)
    """

    def match(self, ride: Ride, candidate_drivers: List[Driver]) -> Optional[Driver]:
        """Return the driver with the lowest weighted score.
        
        Args:
            ride: The ride request to match.
            candidate_drivers: List of available drivers to consider.
            
        Returns:
            The driver with the best combined distance-rating score, or None if no candidates.
        """
        if not candidate_drivers:
            return None

        # Calculate scores for all candidates
        scores = [
            (self._calculate_weighted_score(
                driver.current_location.distance_to(ride.pickup),
                driver.rating,
                ride.passenger_rating
            ), driver)
            for driver in candidate_drivers
        ]

        # Find driver with minimum score
        best_score, best_driver = min(scores, key=lambda x: x[0])
        return best_driver

    def _calculate_weighted_score(
        self,
        distance: float,
        driver_rating: float,
        passenger_rating: float
    ) -> float:
        """Calculate the weighted score for a driver-ride pair.
        
        Args:
            distance: Distance from driver to pickup in kilometers.
            driver_rating: Driver rating (1-5 scale).
            passenger_rating: Passenger rating (1-5 scale).
            
        Returns:
            Weighted composite score (lower is better).
        """
        # Normalize distance: cap at 1.0 if distance exceeds MAX_PICKUP_DISTANCE_KM
        d_norm = min(distance / MAX_PICKUP_DISTANCE_KM, 1.0)

        # Normalize rating difference: scale by MAX_RATING_DIFF (which is 4.0)
        r_norm = abs(driver_rating - passenger_rating) / MAX_RATING_DIFF

        # Compute weighted score
        score = (ScoringEngine.WEIGHT_DISTANCE * d_norm) + (ScoringEngine.WEIGHT_RATING * r_norm)
        return score
