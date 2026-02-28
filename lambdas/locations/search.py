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
        
        # Search query
        sql = "SELECT * FROM Praias WHERE nome LIKE %s AND ativa = 1"
        beaches = execute_query(sql, (f"%{name}%",))
        
        logger.info(f"Found {len(beaches)} beaches matching '{name}'")
        return success(beaches)
        
    except Exception as e:
        logger.error(f"Error searching beaches: {e}")
        return server_error(f"Failed to search beaches: {str(e)}")
