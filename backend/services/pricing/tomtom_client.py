"""
TomTom API client for geocoding and routing.

Provides integration with TomTom APIs for:
- Geocoding: Convert addresses to lat/lon coordinates
- Reverse Geocoding: Convert lat/lon to addresses  
- Autocomplete: Address suggestions as user types
- Routing: Calculate distance and travel time between locations
"""

import httpx
import hashlib
from typing import Optional, Dict, List
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException

from config import (
    TOMTOM_API_KEY,
    TOMTOM_GEOCODE_URL,
    TOMTOM_REVERSE_GEOCODE_URL,
    TOMTOM_AUTOCOMPLETE_URL,
    TOMTOM_ROUTING_URL,
    TOMTOM_TIMEOUT,
    TOMTOM_MAX_RESULTS
)
from models import GeocodingCache


class TomTomClient:
    """Client for TomTom APIs."""
    
    def __init__(self):
        self.api_key = TOMTOM_API_KEY
        self.client = httpx.AsyncClient(timeout=TOMTOM_TIMEOUT)
    
    def _check_api_key(self):
        """Check if API key is configured."""
        if not self.api_key:
            raise HTTPException(
                status_code=503,
                detail="TomTom API key not configured. Set TOMTOM_API_KEY environment variable."
            )
    
    @staticmethod
    def _normalize_address(address: str) -> str:
        """Normalize address for consistent caching."""
        return " ".join(address.lower().split())
    
    @staticmethod
    def _hash_address(address: str) -> str:
        """Generate SHA256 hash of address for cache lookup."""
        normalized = TomTomClient._normalize_address(address)
        return hashlib.sha256(normalized.encode()).hexdigest()
    
    async def geocode(
        self,
        address: str,
        db: Session,
        use_cache: bool = True
    ) -> Dict:
        """
        Geocode an address to latitude/longitude.
        
        Args:
            address: Address string to geocode
            db: Database session for caching
            use_cache: Whether to check cache first (default True)
            
        Returns:
            Dict with geocoding results:
            {
                "latitude": float,
                "longitude": float,
                "formatted_address": str,
                "components": {...},
                "confidence": float,
                "cached": bool
            }
        """
        self._check_api_key()
        
        # Check cache first
        if use_cache:
            address_hash = self._hash_address(address)
            cached = db.query(GeocodingCache).filter(
                GeocodingCache.address_hash == address_hash
            ).first()
            
            if cached:
                # Update usage stats
                cached.last_used_at = datetime.utcnow()
                cached.use_count += 1
                db.commit()
                
                return {
                    "latitude": float(cached.latitude),
                    "longitude": float(cached.longitude),
                    "formatted_address": cached.formatted_address,
                    "components": {
                        "street_number": cached.street_number,
                        "street_name": cached.street_name,
                        "city": cached.city,
                        "state": cached.state,
                        "postal_code": cached.postal_code,
                        "country": cached.country
                    },
                    "confidence": float(cached.confidence_score) if cached.confidence_score else 0,
                    "cached": True
                }
        
        # Call TomTom API
        try:
            params = {
                "key": self.api_key,
                "limit": 1
            }
            
            response = await self.client.get(
                f"{TOMTOM_GEOCODE_URL}/{address}.json",
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            
            if not data.get("results"):
                raise HTTPException(404, f"Address not found: {address}")
            
            result = data["results"][0]
            position = result["position"]
            addr_comp = result.get("address", {})
            
            geocode_result = {
                "latitude": position["lat"],
                "longitude": position["lon"],
                "formatted_address": addr_comp.get("freeformAddress", address),
                "components": {
                    "street_number": addr_comp.get("streetNumber"),
                    "street_name": addr_comp.get("streetName"),
                    "city": addr_comp.get("municipality") or addr_comp.get("municipalitySubdivision"),
                    "state": addr_comp.get("countrySubdivision"),
                    "postal_code": addr_comp.get("postalCode"),
                    "country": addr_comp.get("country")
                },
                "confidence": result.get("score", 0),
                "cached": False
            }
            
            # Cache result
            if use_cache:
                address_hash = self._hash_address(address)
                cache_entry = GeocodingCache(
                    address_text=address,
                    address_hash=address_hash,
                    latitude=geocode_result["latitude"],
                    longitude=geocode_result["longitude"],
                    formatted_address=geocode_result["formatted_address"],
                    street_number=geocode_result["components"]["street_number"],
                    street_name=geocode_result["components"]["street_name"],
                    city=geocode_result["components"]["city"],
                    state=geocode_result["components"]["state"],
                    postal_code=geocode_result["components"]["postal_code"],
                    country=geocode_result["components"]["country"],
                    confidence_score=geocode_result["confidence"]
                )
                
                db.add(cache_entry)
                db.commit()
            
            return geocode_result
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise HTTPException(404, f"Address not found: {address}")
            raise HTTPException(500, f"TomTom API error: {e.response.text}")
        except httpx.TimeoutException:
            raise HTTPException(504, "TomTom API timeout")
        except Exception as e:
            raise HTTPException(500, f"Geocoding error: {str(e)}")
    
    async def reverse_geocode(
        self,
        latitude: float,
        longitude: float
    ) -> Dict:
        """
        Reverse geocode lat/lon to address.
        
        Args:
            latitude: Latitude
            longitude: Longitude
            
        Returns:
            Dict with address components
        """
        self._check_api_key()
        
        try:
            params = {
                "key": self.api_key
            }
            
            response = await self.client.get(
                f"{TOMTOM_REVERSE_GEOCODE_URL}/{latitude},{longitude}.json",
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            
            if not data.get("addresses"):
                raise HTTPException(404, "Address not found for coordinates")
            
            addr = data["addresses"][0]["address"]
            
            return {
                "formatted_address": addr.get("freeformAddress", ""),
                "street_number": addr.get("streetNumber"),
                "street_name": addr.get("streetName"),
                "city": addr.get("municipality") or addr.get("municipalitySubdivision"),
                "state": addr.get("countrySubdivision"),
                "postal_code": addr.get("postalCode"),
                "country": addr.get("country")
            }
            
        except httpx.HTTPStatusError as e:
            raise HTTPException(500, f"TomTom API error: {e.response.text}")
        except httpx.TimeoutException:
            raise HTTPException(504, "TomTom API timeout")
        except Exception as e:
            raise HTTPException(500, f"Reverse geocoding error: {str(e)}")
    
    async def autocomplete(
        self,
        query: str,
        center_lat: Optional[float] = None,
        center_lon: Optional[float] = None
    ) -> List[Dict]:
        """
        Get address suggestions as user types.
        
        Args:
            query: Partial address string
            center_lat: Center latitude for biasing results
            center_lon: Center longitude for biasing results
            
        Returns:
            List of address suggestions
        """
        self._check_api_key()
        
        try:
            params = {
                "key": self.api_key,
                "limit": TOMTOM_MAX_RESULTS,
                "typeahead": True
            }
            
            if center_lat and center_lon:
                params["lat"] = center_lat
                params["lon"] = center_lon
            
            response = await self.client.get(
                f"{TOMTOM_AUTOCOMPLETE_URL}/{query}.json",
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            
            suggestions = []
            for result in data.get("results", []):
                addr = result.get("address", {})
                position = result.get("position", {})
                suggestions.append({
                    "address": addr.get("freeformAddress", ""),
                    "city": addr.get("municipality"),
                    "state": addr.get("countrySubdivision"),
                    "postal_code": addr.get("postalCode"),
                    "country": addr.get("country"),
                    "latitude": position.get("lat"),
                    "longitude": position.get("lon")
                })
            
            return suggestions
            
        except httpx.HTTPStatusError as e:
            raise HTTPException(500, f"TomTom API error: {e.response.text}")
        except httpx.TimeoutException:
            raise HTTPException(504, "TomTom API timeout")
        except Exception as e:
            raise HTTPException(500, f"Autocomplete error: {str(e)}")
    
    async def calculate_route(
        self,
        origin_lat: float,
        origin_lon: float,
        dest_lat: float,
        dest_lon: float
    ) -> Dict:
        """
        Calculate route between two points.
        
        Args:
            origin_lat: Origin latitude
            origin_lon: Origin longitude
            dest_lat: Destination latitude
            dest_lon: Destination longitude
            
        Returns:
            Dict with route details:
            {
                "distance_miles": float,
                "duration_minutes": float,
                "traffic_delay_minutes": float
            }
        """
        self._check_api_key()
        
        try:
            # Format coordinates as lat,lon:lat,lon
            locations = f"{origin_lat},{origin_lon}:{dest_lat},{dest_lon}"
            
            params = {
                "key": self.api_key,
                "traffic": True,  # Include traffic data
                "travelMode": "car"
            }
            
            response = await self.client.get(
                f"{TOMTOM_ROUTING_URL}/{locations}/json",
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            
            if not data.get("routes"):
                raise HTTPException(404, "No route found")
            
            route = data["routes"][0]
            summary = route["summary"]
            
            # Convert meters to miles
            distance_miles = summary["lengthInMeters"] / 1609.34
            
            # Convert seconds to minutes
            duration_minutes = summary["travelTimeInSeconds"] / 60
            
            traffic_delay_minutes = 0
            if "trafficDelayInSeconds" in summary:
                traffic_delay_minutes = summary["trafficDelayInSeconds"] / 60
            
            return {
                "distance_miles": round(distance_miles, 2),
                "duration_minutes": round(duration_minutes, 1),
                "traffic_delay_minutes": round(traffic_delay_minutes, 1)
            }
            
        except httpx.HTTPStatusError as e:
            raise HTTPException(500, f"TomTom API error: {e.response.text}")
        except httpx.TimeoutException:
            raise HTTPException(504, "TomTom API timeout")
        except Exception as e:
            raise HTTPException(500, f"Routing error: {str(e)}")
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
