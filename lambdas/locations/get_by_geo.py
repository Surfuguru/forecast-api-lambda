"""
Get beaches by geographic coordinates
GET /geolocation/nearest-spots?lat=-22.9&long=-43.2&range=50
"""

import json
import logging
from common.db import execute_query
from common.responses import success, bad_request, server_error

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    Get nearest beaches by coordinates
    """
    try:
        # Parse query parameters
        params = event.get('queryStringParameters', {}) or {}
        
        lat = params.get('lat')
        long = params.get('long')
        range_km = params.get('range', '50')
        
        # Validate parameters
        if not lat or not long:
            return bad_request('Missing required parameters: lat, long')
        
        try:
            lat = float(lat)
            long = float(long)
            range_km = float(range_km)
        except ValueError:
            return bad_request('Invalid parameter types - must be numbers')
        
        logger.info(f"Searching beaches near lat={lat}, long={long}, range={range_km}km")
        
        # Haversine formula for distance calculation
        sql = f"""
            SELECT 
                *,
                (
                    6371 * acos(
                        cos(radians({lat})) 
                        * cos(radians(lat)) 
                        * cos(radians(lon) - radians({long})) 
                        + sin(radians({lat})) 
                        * sin(radians(lat))
                    )
                ) AS distance
            FROM Praias
            WHERE ativa = 1
            HAVING distance < {range_km}
            ORDER BY distance
        """
        
        beaches = execute_query(sql)
        
        logger.info(f"Found {len(beaches)} beaches within {range_km}km")
        return success(beaches)
        
    except Exception as e:
        logger.error(f"Error searching beaches: {e}")
        return server_error(f"Failed to search beaches: {str(e)}")
