"""Ride-driver matching strategies package.

This package provides different algorithms for matching rides to drivers based
on various criteria (distance, rating, etc.).
"""

from src.strategies.base import BaseStrategy
from src.strategies.shortest import ShortestDistanceStrategy
from src.strategies.weighted import WeightedScoreStrategy, ScoringEngine

__all__ = [
    "BaseStrategy",
    "ShortestDistanceStrategy",
    "WeightedScoreStrategy",
    "ScoringEngine",
]
