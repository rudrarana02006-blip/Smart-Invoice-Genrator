"""
Analytics Routes — RBAC-enabled analytics and geospatial summary.
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional
from auth import get_approved_user
from database import get_invoice_collection, get_user_collection
from models.user import UserRole
from datetime import datetime, timezone
import collections
import google.generativeai as genai
import os
import json
import re
from config import settings
try:
    from geopy.geocoders import Nominatim, GoogleV3
    from geopy.exc import GeocoderTimedOut, GeocoderServiceError
    GEOPY_AVAILABLE = True
except ImportError:
    print("⚠️ WARNING: geopy not found. Map geocoding will be limited.")
    GEOPY_AVAILABLE = False
    class GeocoderTimedOut(Exception): pass
    class GeocoderServiceError(Exception): pass

# Setup Geocoding Fallback via Gemini (Compatible SDK)
if not os.getenv("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY") == "your_gemini_api_key_here":
    genai.configure(api_key="MISSING")
else:
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Use Gemini 1.5 Pro for maximum geospatial intelligence
geo_model = genai.GenerativeModel(model_name='gemini-1.5-pro')

router = APIRouter()

# Simple City to Lat/Lng Mapping Helper
CITY_COORDS = {
    # Tier 1 & 2
    # Tier 1 & 2
    "delhi": [28.6139, 77.2090],
    "mumbai": [19.0760, 72.8777],
    "bangalore": [12.9716, 77.5946],
    "bengaluru": [12.9716, 77.5946],
    "chennai": [13.0827, 80.2707],
    "kolkata": [22.5726, 88.3639],
    "hyderabad": [17.3850, 78.4867],
    "pune": [18.5204, 73.8567],
    "ahmedabad": [23.0225, 72.5714],
    "jaipur": [26.9124, 75.7873],
    "lucknow": [26.8467, 80.9462],
    "surat": [21.1702, 72.8311],
    "chandigarh": [30.7333, 76.7794],
    "sahibabad": [28.6738, 77.3411],
    
    # NCR & North
    "gurgaon": [28.4595, 77.0266],
    "gurugram": [28.4595, 77.0266],
    "noida": [28.5355, 77.3910],
    "ghaziabad": [28.6692, 77.4538],
    "faridabad": [28.4089, 77.3178],
    "kanpur": [26.4499, 80.3319],
    "agra": [27.1767, 78.0081],
    "ludhiana": [30.9010, 75.8573],
    "amritsar": [31.6340, 74.8723],
    
    # Bihar & East
    "patna": [25.5941, 85.1376],
    "bihar": [25.0961, 85.3131],
    "gaya": [24.7914, 85.0002],
    "muzaffarpur": [26.1209, 85.3647],
    "ranchi": [23.3441, 85.3096],
    "jamshedpur": [22.8046, 86.2029],
    "bhubaneswar": [20.2961, 85.8245],
    "guwahati": [26.1445, 91.7362],
    
    # Central & West
    "indore": [22.7196, 75.8577],
    "bhopal": [23.2599, 77.4126],
    "nagpur": [21.1458, 79.0882],
    "vadodara": [22.3072, 73.1812],
    "rajkot": [22.3039, 70.8022],
    
    # South
    "kochi": [9.9312, 76.2673],
    "coimbatore": [11.0168, 76.9558],
    "visakhapatnam": [17.6868, 83.2185],
    "madurai": [9.9252, 78.1198],
    
    # International
    "san francisco": [37.7749, -122.4194],
    "new york": [40.7128, -74.0060],
    "london": [51.5074, -0.1278],
    "dubai": [25.2048, 55.2708],
    "singapore": [1.3521, 103.8198]
}

# Initialize Geocoders: Google Maps (Priority) & OpenStreetMap (Fallback)
google_geocoder = None
osm_geocoder = None

if GEOPY_AVAILABLE:
    try:
        if settings.GOOGLE_MAPS_API_KEY:
            google_geocoder = GoogleV3(api_key=settings.GOOGLE_MAPS_API_KEY)
        osm_geocoder = Nominatim(user_agent="smart_invoice_generator")
    except:
        pass

async def get_cached_coords(address):
    """
    Get Latitude/Longitude for an address using professional geocoding:
    Checks cache first, then Google Maps/OSM.
    """
    if not address or len(address) < 3:
        return None, None
        
    from database import get_db
    db = get_db()
    cache_coll = db["geo_cache"]
    
    addr_lower = address.lower().strip()
    words = addr_lower.split()
    cache_key = " ".join(words[-4:]) if len(words) >= 4 else addr_lower
    
    # 1. Check Cache
    cached = await cache_coll.find_one({"_id": cache_key})
    if cached:
        return cached["coords"], cached.get("name", "Unknown Location")
        
    # 2. Professional Geocoding
    try:
        location = None
        if google_geocoder:
            location = google_geocoder.geocode(address, timeout=10)
        if not location:
            location = osm_geocoder.geocode(address, timeout=10)
            
        if location:
            coords = [location.latitude, location.longitude]
            city_name = location.address.split(',')[0]
            await cache_coll.insert_one({
                "_id": cache_key, 
                "coords": coords,
                "name": city_name,
                "source": "pro"
            })
            return coords, city_name
            
    except Exception as e:
        print(f"DEBUG: Professional Geocoding failed: {e}")

    # 3. Failsafe: Local Dictionary
    for city, coords in CITY_COORDS.items():
        if city in words:
            return coords, city.title()
            
    return None, None

@router.get("/summary")
async def get_analytics_summary(
    user_id: Optional[str] = Query(None),
    current_user: dict = Depends(get_approved_user)
):
    """
    Returns aggregated analytics summary and heatmap data.
    RBAC: Admins can filter by user_id; Users are restricted to their own data.
    """
    invoices_coll = get_invoice_collection()
    org_id = current_user.get("org_id")
    
    # Base match query
    match_query = {"org_id": org_id}
    
    # RBAC Enforcement
    if current_user.get("role") == UserRole.ADMIN:
        if user_id:
            # Resolve user_id to email since created_by stores email
            users_coll = get_user_collection()
            from bson import ObjectId
            try:
                target_user = await users_coll.find_one({"_id": ObjectId(user_id), "org_id": org_id})
                if target_user:
                    match_query["created_by"] = target_user["email"]
                else:
                    raise HTTPException(status_code=404, detail="User not found")
            except:
                raise HTTPException(status_code=400, detail="Invalid user ID format")
    else:
        # Standard user is strictly filtered by their own email
        match_query["created_by"] = current_user["email"]

    # 1. Stats Aggregation (Monthly & Status)
    pipeline = [
        {"$match": match_query},
        {
            "$facet": {
                "status_counts": [
                    {"$group": {"_id": "$status", "count": {"$sum": 1}, "total_amount": {"$sum": "$grand_total"}}}
                ],
                "monthly_revenue": [
                    {
                        "$project": {
                            "month": {"$month": "$created_at"},
                            "year": {"$year": "$created_at"},
                            "grand_total": 1,
                            "status": 1
                        }
                    },
                    {"$match": {"status": "paid"}},
                    {
                        "$group": {
                            "_id": {"month": "$month", "year": "$year"},
                            "revenue": {"$sum": "$grand_total"}
                        }
                    },
                    {"$sort": {"_id.year": 1, "_id.month": 1}}
                ],
                "map_data": [
                    {"$project": {"client_address": 1, "grand_total": 1}},
                    {"$match": {"client_address": {"$ne": None}}}
                ]
            }
        }
    ]
    
    results = await invoices_coll.aggregate(pipeline).to_list(1)
    results = results[0] if results else {}

    # Process Map Data (Geospatial Heatmap)
    heatmap_points = []
    for doc in results.get("map_data", []):
        coords, city_name = await get_cached_coords(doc.get("client_address", ""))
        if coords:
            heatmap_points.append({
                "lat": coords[0],
                "lng": coords[1],
                "city": city_name,
                "weight": doc.get("grand_total", 0)
            })

    # Final response structure
    return {
        "stats": results.get("status_counts", []),
        "monthly_revenue": results.get("monthly_revenue", []),
        "heatmap": heatmap_points
    }
