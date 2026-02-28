"""
Legacy forecast endpoint
GET /forecast?praia_id={id}
GET /forecast/{pais}/{estado}/{municipio}?praia={praia}
"""

import json
import logging
import boto3
from botocore.exceptions import ClientError
from common.db import execute_query
from common.responses import success, bad_request, not_found, server_error

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# S3 client (initialized outside handler for reuse)
s3_client = None

def get_s3_client():
    """Get or create S3 client"""
    global s3_client
    if s3_client is None:
        import os
        s3_client = boto3.client(
            's3',
            aws_access_key_id=os.environ.get('FORECAST_API_AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.environ.get('FORECAST_API_AWS_SECRET_ACCESS_KEY'),
            region_name='us-east-1'
        )
    return s3_client


def get_s3_object(bucket, key):
    """Fetch object from S3"""
    try:
        client = get_s3_client()
        response = client.get_object(Bucket=bucket, Key=key)
        data = json.loads(response['Body'].read().decode('utf-8'))
        logger.info(f"S3_OBJECT_FETCHED: bucket={bucket}, key={key}")
        return data
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            logger.warning(f"S3_OBJECT_NOT_FOUND: bucket={bucket}, key={key}")
            return None
        logger.error(f"S3_ERROR: {e}")
        raise


def get_atmospheric_data(spot_id):
    """Fetch atmospheric forecast from S3"""
    import os
    bucket = os.environ.get('FORECAST_API_AWS_FORECAST_BUCKET')
    key = f"atmos/atmos{spot_id}pro.json"
    return get_s3_object(bucket, key)


def get_oceanic_data(spot_id):
    """Fetch oceanic forecast from S3"""
    import os
    bucket = os.environ.get('FORECAST_API_AWS_FORECAST_BUCKET')
    key = f"oceanos/oceano{spot_id}.json"
    return get_s3_object(bucket, key)


def get_surf_data(spot_id):
    """Fetch surf/beach forecast from S3"""
    import os
    bucket = os.environ.get('FORECAST_API_AWS_FORECAST_BUCKET')
    key = f"oceanos/praia{spot_id}.json"
    return get_s3_object(bucket, key)


def lambda_handler(event, context):
    """
    Legacy forecast endpoint
    """
    import os
    request_id = f"{int(time.time() * 1000)}-{os.urandom(4).hex()}"
    
    try:
        logger.info(f"LEGACY_FORECAST_REQUEST: {request_id}")
        
        # Parse parameters
        params = event.get('queryStringParameters', {}) or {}
        path_params = event.get('pathParameters', {}) or {}
        
        # Extract from query string
        praia_id = params.get('praia_id')
        pais = params.get('pais')
        estado = params.get('estado')
        municipio = params.get('municipio')
        praia = params.get('praia')
        
        # Try to extract from path (format: /forecast/{pais}/{estado}/{municipio})
        path = event.get('path', '')
        path_parts = [p for p in path.split('/') if p and p != 'forecast']
        
        if len(path_parts) >= 3:
            pais = pais or path_parts[0]
            estado = estado or path_parts[1]
            municipio = municipio or path_parts[2]
        
        # Validate parameters
        if not praia_id and not (pais and estado and municipio):
            return bad_request(
                'Missing required parameters. Use either: '
                '/forecast/{pais}/{estado}/{municipio}?praia={praia} '
                'OR /forecast?praia_id={id}'
            )
        
        # Get location data
        litoral_id = None
        spot_type = 'OCEANIC'
        
        if praia_id:
            # Direct beach lookup
            sql = "SELECT * FROM praias WHERE id = %s"
            result = execute_query(sql, (praia_id,))
            
            if not result:
                return not_found(f'Beach with id {praia_id} not found')
            
            location_data = result[0]
            litoral_id = location_data.get('litoral_id')
            spot_type = 'SURF'
            
        elif praia:
            # Search beach by name
            sql = "SELECT * FROM praias WHERE nome_2 LIKE %s LIMIT 1"
            result = execute_query(sql, (f"%{praia}%",))
            
            if result:
                location_data = result[0]
                litoral_id = location_data.get('litoral_id')
                spot_type = 'SURF'
        
        if not litoral_id and pais and estado and municipio:
            # Get municipality
            sql = """
                SELECT l.id, l.litoral_id 
                FROM locais l 
                WHERE l.nome = %s AND l.nivel = 4
            """
            result = execute_query(sql, (municipio,))
            
            if result:
                litoral_id = result[0].get('litoral_id')
        
        if not litoral_id:
            return not_found('Location not found')
        
        logger.info(f"LOCATION_RESOLVED: litoral_id={litoral_id}, spot_type={spot_type}")
        
        # Fetch atmospheric data
        atmospheric_data = get_atmospheric_data(litoral_id)
        
        # Fetch forecast data based on spot type
        if spot_type == 'SURF':
            forecast_data = get_surf_data(litoral_id)
        else:
            forecast_data = get_oceanic_data(litoral_id)
        
        if not atmospheric_data and not forecast_data:
            return not_found('Forecast data not available for this location')
        
        # Build simplified forecast response
        forecast = {
            'id': str(litoral_id),
            'type': spot_type,
            'name': location_data.get('nome_2', location_data.get('nome', 'Unknown')) if praia_id or praia else f'Location {litoral_id}',
            'date': forecast_data.get('date') if forecast_data else None,
            'forecast': {
                'atmospheric': atmospheric_data.get('dados') if atmospheric_data else None,
                'oceanic': forecast_data.get('dados') if forecast_data else None
            }
        }
        
        logger.info(f"LEGACY_FORECAST_SUCCESS: request_id={request_id}")
        return success(forecast)
        
    except Exception as e:
        logger.error(f"LEGACY_FORECAST_ERROR: {str(e)}")
        return server_error(f"Failed to fetch forecast: {str(e)}")


import time
