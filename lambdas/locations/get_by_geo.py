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
        
        # Use the exact query from original TypeScript code
        sql = f"""
            SELECT 
                pr.id as praia_id,
                pr.nome_2 AS praia_nome,
                lo.litoral_id as litoral_id,
                lo.nome as litoral_nome,
                lo.lat as litoral_lat,
                lo.lon as litoral_lon,
                pr.lat as lat,
                pr.lon as lon,
                (SELECT lo2.sigla FROM locais lo2 WHERE lo2.id = lo.pai) as uf,
                ((3956 *
                2 *
                ASIN(
                    SQRT(POWER(SIN((abs({lat}) - abs(pr.lat)) *
                               pi()/180 / 2),2) +
                    COS(abs({long}) * pi()/180 ) *
                    COS(abs(pr.lat) * pi()/180) *
                    POWER(SIN((abs({long}) - abs(pr.lon)) *
                                pi()/180 / 2), 2))
                    )
                ) * 1.609344) as distancia
            FROM praias pr
            INNER JOIN locais lo ON lo.id = pr.local_id
            HAVING distancia < {range_km}
            ORDER BY distancia
            LIMIT 100
        """
        
        beaches = execute_query(sql)
        
        logger.info(f"Found {len(beaches)} beaches within {range_km}km")
        return success(beaches)
        
    except Exception as e:
        logger.error(f"Error searching beaches: {e}")
        return server_error(f"Failed to search beaches: {str(e)}")
