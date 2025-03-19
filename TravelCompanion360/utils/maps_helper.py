import os
import requests
import logging

GOOGLE_MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY")

def get_coordinates(location):
    """
    Get latitude and longitude coordinates for a location using Google Maps Geocoding API
    
    Args:
        location (str): Location to geocode
        
    Returns:
        dict: Dictionary with lat and lng keys, or None if unsuccessful
    """
    if not GOOGLE_MAPS_API_KEY:
        logging.error("Google Maps API key not found")
        return None
        
    try:
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {
            "address": location,
            "key": GOOGLE_MAPS_API_KEY
        }
        
        response = requests.get(url, params=params)
        data = response.json()
        
        if data["status"] == "OK" and len(data["results"]) > 0:
            location = data["results"][0]["geometry"]["location"]
            return {
                "lat": location["lat"],
                "lng": location["lng"]
            }
        else:
            logging.error(f"Geocoding error: {data['status']}")
            return None
            
    except Exception as e:
        logging.error(f"Error getting coordinates: {e}")
        return None

def get_nearby_places(lat, lng, place_type, radius=5000):
    """
    Get nearby places of a specific type using Google Places API
    
    Args:
        lat (float): Latitude
        lng (float): Longitude
        place_type (str): Type of place (e.g., 'hotel', 'restaurant')
        radius (int): Search radius in meters
        
    Returns:
        list: List of nearby places or None if unsuccessful
    """
    if not GOOGLE_MAPS_API_KEY:
        logging.error("Google Maps API key not found")
        return None
        
    try:
        url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        params = {
            "location": f"{lat},{lng}",
            "radius": radius,
            "type": place_type,
            "key": GOOGLE_MAPS_API_KEY
        }
        
        response = requests.get(url, params=params)
        data = response.json()
        
        if data["status"] == "OK":
            return data["results"]
        else:
            logging.error(f"Places API error: {data['status']}")
            return None
            
    except Exception as e:
        logging.error(f"Error getting nearby places: {e}")
        return None
