"""Global constants, time utilities, and geospatial functions for the ride-share simulator."""

from datetime import datetime, timezone
from typing import List
import math

import pygeohash


# ==================== Module-Level Constants ====================

GEOHASH_PRECISION: int = 5
BASE_SPEED_KMH: float = 30.0
MAX_PICKUP_DISTANCE_KM: float = 10.0
MAX_RATING_DIFF: float = 4.0
EARTH_RADIUS_KM: float = 6371.0
RIDE_REQUEST_TIMEOUT_SECONDS: float = 300.0

# ==================== Time Conversion Functions ====================


def iso8601_to_seconds(timestamp_str: str) -> float:
    """Convert ISO-8601 timestamp string to Unix seconds.
    
    Args:
        timestamp_str: ISO-8601 formatted string (e.g., "2024-05-19T10:30:00Z")
        
    Returns:
        Unix timestamp in seconds (float).
        
    Raises:
        ValueError: If the timestamp string is not in valid ISO-8601 format.
    """
    try:
        dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        return dt.timestamp()
    except (ValueError, AttributeError) as e:
        raise ValueError(f"Invalid ISO-8601 timestamp: {timestamp_str}") from e


def seconds_to_iso8601(seconds: float) -> str:
    """Convert Unix seconds to ISO-8601 timestamp string.
    
    Args:
        seconds: Unix timestamp in seconds (float).
        
    Returns:
        ISO-8601 formatted string with 'Z' suffix for UTC.
    """
    dt = datetime.fromtimestamp(seconds, tz=timezone.utc)
    return dt.isoformat(timespec="seconds").replace("+00:00", "Z")


def is_timed_out(
    request_time_seconds: float,
    current_time_seconds: float,
    timeout_seconds: float = RIDE_REQUEST_TIMEOUT_SECONDS,
) -> bool:
    """Check if a ride request has exceeded its timeout window.
    
    Args:
        request_time_seconds: Original request time in Unix seconds.
        current_time_seconds: Current simulation time in Unix seconds.
        timeout_seconds: Maximum wait time allowed (default 300s).
        
    Returns:
        True if wait time exceeds timeout, False otherwise.
    """
    return (current_time_seconds - request_time_seconds) > timeout_seconds


def format_duration(seconds: float) -> str:
    """Convert seconds to human-readable HH:MM:SS format.
    
    Args:
        seconds: Duration in seconds (float).
        
    Returns:
        Formatted string as "HH:MM:SS".
    """
    total_seconds = int(seconds)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


# ==================== Geospatial Functions ====================


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate great-circle distance between two coordinates in kilometers.
    
    Uses the Haversine formula to compute the shortest distance on the Earth's surface.
    
    Args:
        lat1: Latitude of first point in degrees.
        lon1: Longitude of first point in degrees.
        lat2: Latitude of second point in degrees.
        lon2: Longitude of second point in degrees.
        
    Returns:
        Distance in kilometers.
    """
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return EARTH_RADIUS_KM * c


def get_nearby_geohashes(geohash: str) -> List[str]:
    """Get the 9-cell geohash neighborhood (cell + 8 adjacent neighbors).
    
    Args:
        geohash: The central geohash string.
        
    Returns:
        List of 9 geohash strings (center + 8 neighbors).
        
    Raises:
        ValueError: If the geohash is invalid or empty.
    """
    if not geohash or not isinstance(geohash, str):
        raise ValueError("Geohash must be a non-empty string.")

    neighbors_list = [geohash]  # Start with the center cell
    
    try:
        # Get the 4 cardinal neighbors
        right = pygeohash.neighbor.get_adjacent(geohash, "right")
        left = pygeohash.neighbor.get_adjacent(geohash, "left")
        top = pygeohash.neighbor.get_adjacent(geohash, "top")
        bottom = pygeohash.neighbor.get_adjacent(geohash, "bottom")
        
        neighbors_list.extend([right, left, top, bottom])
        
        # Get the 4 diagonal neighbors by combining cardinal directions
        top_right = pygeohash.neighbor.get_adjacent(top, "right")
        top_left = pygeohash.neighbor.get_adjacent(top, "left")
        bottom_right = pygeohash.neighbor.get_adjacent(bottom, "right")
        bottom_left = pygeohash.neighbor.get_adjacent(bottom, "left")
        
        neighbors_list.extend([top_right, top_left, bottom_right, bottom_left])
        
    except (ValueError, AttributeError):
        # If neighbor calculation fails, return at least the center cell
        pass
    
    return neighbors_list
