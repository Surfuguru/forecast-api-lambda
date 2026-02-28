"""
Legacy forecast endpoint - Simplified version without S3
GET /forecast?praia_id={id}
"""

import json
import logging
from common.db import execute_query
from common.responses import success, bad_request, not_found, server_error

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    """
    Legacy forecast endpoint - returns beach data from database
    """
    try:
        logger.info("LEGACY_FORECAST_REQUEST")
        
        # Parse parameters
        params = event.get('queryStringParameters', {}) or {}
        praia_id = params.get('praia_id')
        
        # Validate
        if not praia_id:
            return bad_request('Missing required parameter: praia_id')
        
        # Get beach data from database
        sql = """
            SELECT DISTINCT
                lo.litoral_id AS litoral_id,
                lo.nome as litoral_nome,
                lo.lat as litoral_lat,
                lo.lon as litoral_lon,
                pr.id AS praia_id,
                pr.litoral_id AS vento_litoraneo_id,
                pr.orientacao as orientacao,
                pr.nome_2 AS nome,
                pr.lat as lat,
                pr.lon as lon,
                (SELECT lo2.sigla FROM locais lo2 WHERE lo2.id = lo.pai) as uf
            FROM praias pr 
            INNER JOIN locais lo ON pr.local_id = lo.id
            WHERE pr.id = %s
        """
        
        result = execute_query(sql, (praia_id,))
        
        if not result:
            return not_found(f'Beach with id {praia_id} not found')
        
        beach = result[0]
        
        # Build simplified forecast response
        forecast = {
            'id': str(beach['praia_id']),
            'type': 'SURF',
            'name': beach['nome'],
            'litoral_id': beach['litoral_id'],
            'litoral_nome': beach['litoral_nome'],
            'coordinates': {
                'lat': float(beach['lat']) if beach['lat'] else None,
                'long': float(beach['lon']) if beach['lon'] else None
            },
            'uf': beach['uf'],
            'orientacao': beach['orientacao'],
            'message': 'Simplified forecast - atmospheric/oceanic data not available in this version'
        }
        
        logger.info(f"LEGACY_FORECAST_SUCCESS: praia_id={praia_id}")
        return success(forecast)
        
    except Exception as e:
        logger.error(f"LEGACY_FORECAST_ERROR: {str(e)}")
        return server_error(f"Failed to fetch forecast: {str(e)}")
