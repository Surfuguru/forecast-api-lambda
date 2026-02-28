"""
Search beaches by name
GET /geolocation/search?name=saquarema
"""

import json
import logging
from common.db import execute_query
from common.responses import success, bad_request, server_error

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    Search beaches by name
    """
    try:
        # Parse query parameters
        params = event.get('queryStringParameters', {}) or {}
        
        name = params.get('name')
        
        # Validate parameters
        if not name:
            return bad_request('Missing required parameter: name')
        
        logger.info(f"Searching beaches with name: {name}")
        
        # Search query - using MATCH AGAINST for full-text search
        sql = f"""
            SELECT DISTINCT
                lo.litoral_id AS litoral_id,
                lo.nome as litoral_nome,
                lo.lat as litoral_lat,
                lo.lon as litoral_lon,
                pr.id AS praia_id,
                pr.nome_2 AS praia_nome,
                pr.lat as lat,
                pr.lon as lon,
                (SELECT lo2.sigla FROM locais lo2 WHERE lo2.id = lo.pai) as uf
            FROM locais lo
            INNER JOIN praias pr ON pr.local_id = lo.id
            WHERE MATCH (lo.localizacao) AGAINST ('{name}')
            UNION
            SELECT DISTINCT
                lo.litoral_id AS litoral_id,
                lo.nome as litoral_nome,
                lo.lat as litoral_lat,
                lo.lon as litoral_lon,
                pr.id AS praia_id,
                pr.nome_2 AS praia_nome,
                pr.lat as lat,
                pr.lon as lon,
                (SELECT lo2.sigla FROM locais lo2 WHERE lo2.id = lo.pai) as uf
            FROM praias pr 
            INNER JOIN locais lo ON pr.local_id = lo.id
            WHERE MATCH (pr.nome) AGAINST ('{name}')
        """
        beaches = execute_query(sql)
        
        logger.info(f"Found {len(beaches)} beaches matching '{name}'")
        return success(beaches)
        
    except Exception as e:
        logger.error(f"Error searching beaches: {e}")
        return server_error(f"Failed to search beaches: {str(e)}")
