import math
from config import AVERAGE_SPEED_KMH

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points 
    on the earth in kilometers using the Haversine formula.
    """
    R = 6371.0  # Earth's radius in kilometers

    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def urban_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Estimate urban road network travel distance in kilometers.
    Applies a Manhattan/circuity factor (1.3x) to Haversine straight-line distance.
    """
    straight_dist = haversine_distance(lat1, lon1, lat2, lon2)
    return straight_dist * 1.30

def calculate_travel_time_min(distance_km: float, speed_kmh: float = AVERAGE_SPEED_KMH) -> float:
    """
    Calculate travel time in minutes given distance in km and speed in km/h.
    """
    if speed_kmh <= 0:
        return 0.0
    return (distance_km / speed_kmh) * 60.0
