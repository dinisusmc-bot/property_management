"""
Distance calculation service using Google Maps API
"""
import httpx
import logging
from typing import List, Tuple
import config

logger = logging.getLogger(__name__)

class DistanceService:
    """Calculate distances between locations"""
    
    def __init__(self):
        self.api_key = config.GOOGLE_MAPS_API_KEY
        self.api_url = config.GOOGLE_MAPS_API_URL
        self.use_fallback = not self.api_key  # Use estimated distances if no API key
    
    async def calculate_distance(self, origin: str, destination: str) -> float:
        """
        Calculate distance between two locations
        
        Args:
            origin: Starting location (address or city, state)
            destination: Ending location (address or city, state)
        
        Returns:
            Distance in miles
        """
        if self.use_fallback:
            # Fallback: estimate based on string similarity (for demo purposes)
            return self._estimate_distance(origin, destination)
        
        try:
            async with httpx.AsyncClient() as client:
                params = {
                    "origins": origin,
                    "destinations": destination,
                    "units": "imperial",  # Miles
                    "key": self.api_key
                }
                
                response = await client.get(self.api_url, params=params, timeout=10.0)
                response.raise_for_status()
                
                data = response.json()
                
                if data["status"] == "OK":
                    element = data["rows"][0]["elements"][0]
                    if element["status"] == "OK":
                        # Distance is in meters, convert to miles
                        distance_meters = element["distance"]["value"]
                        distance_miles = distance_meters * 0.000621371
                        return round(distance_miles, 2)
                
                logger.warning(f"Google Maps API error: {data.get('status')}")
                return self._estimate_distance(origin, destination)
                
        except Exception as e:
            logger.error(f"Error calculating distance: {e}")
            return self._estimate_distance(origin, destination)
    
    def _estimate_distance(self, origin: str, destination: str) -> float:
        """
        Fallback distance estimation (for demo without API key)
        
        This is a simple estimation based on common routes.
        In production, you would use the Google Maps API.
        """
        # Common city pairs and their approximate distances
        routes = {
            ("new york", "boston"): 215,
            ("new york", "philadelphia"): 95,
            ("new york", "washington"): 225,
            ("los angeles", "san francisco"): 380,
            ("chicago", "detroit"): 280,
            ("miami", "orlando"): 235,
        }
        
        # Normalize locations
        origin_norm = origin.lower().split(",")[0].strip()
        dest_norm = destination.lower().split(",")[0].strip()
        
        # Check if route exists in either direction
        key1 = (origin_norm, dest_norm)
        key2 = (dest_norm, origin_norm)
        
        if key1 in routes:
            return float(routes[key1])
        elif key2 in routes:
            return float(routes[key2])
        
        # Default estimate: 100 miles for unknown routes
        logger.info(f"Using default distance estimate for {origin} -> {destination}")
        return 100.0
    
    async def calculate_route_distance(self, stops: List[str]) -> Tuple[float, List[float]]:
        """
        Calculate total distance for multi-stop route
        
        Args:
            stops: List of locations in order
        
        Returns:
            Tuple of (total_distance, list of segment distances)
        """
        if len(stops) < 2:
            return 0.0, []
        
        total_distance = 0.0
        segment_distances = []
        
        for i in range(len(stops) - 1):
            distance = await self.calculate_distance(stops[i], stops[i + 1])
            segment_distances.append(distance)
            total_distance += distance
        
        return round(total_distance, 2), segment_distances
