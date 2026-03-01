"""
Legacy forecast endpoint - Full version with S3 integration
GET /forecast?praia_id={id}
"""

import json
import logging
import boto3
import os
from botocore.exceptions import ClientError
from common.db import execute_query
from common.responses import success, bad_request, not_found, server_error

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Global S3 client (reused across invocations)
_s3_client = None

def get_s3_client():
    """Get or create S3 client"""
    global _s3_client
    if _s3_client is None:
        _s3_client = boto3.client(
            's3',
            aws_access_key_id=os.environ.get('FORECAST_API_AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.environ.get('FORECAST_API_AWS_SECRET_ACCESS_KEY'),
            region_name='us-east-1'
        )
        logger.info("S3 client created")
    return _s3_client


def fetch_s3_object(bucket, key):
    """Fetch JSON object from S3"""
    try:
        client = get_s3_client()
        response = client.get_object(Bucket=bucket, Key=key)
        data = json.loads(response['Body'].read().decode('utf-8'))
        logger.info(f"S3 object fetched: bucket={bucket}, key={key}")
        return data
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            logger.warning(f"S3 object not found: bucket={bucket}, key={key}")
            return None
        logger.error(f"S3 error: {e}")
        raise
    except Exception as e:
        logger.error(f"Error fetching S3 object: {e}")
        raise


def lambda_handler(event, context):
    """
    Legacy forecast endpoint with full S3 integration
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
        litoral_id = beach['litoral_id']
        
        logger.info(f"LOCATION_RESOLVED: praia_id={praia_id}, litoral_id={litoral_id}")
        
        # Fetch atmospheric data from S3
        bucket = os.environ.get('FORECAST_API_AWS_FORECAST_BUCKET', 'previsao')
        atmos_key = f"atmos/atmos{litoral_id}pro.json"
        
        atmospheric_data = None
        try:
            atmospheric_data = fetch_s3_object(bucket, atmos_key)
            if atmospheric_data:
                logger.info(f"Atmospheric data fetched for litoral {litoral_id}")
        except Exception as e:
            logger.warning(f"Could not fetch atmospheric data: {e}")
        
        # Fetch oceanic/beach data from S3
        oceanic_key = f"oceanos/praia{praia_id}.json"
        
        oceanic_data = None
        try:
            oceanic_data = fetch_s3_object(bucket, oceanic_key)
            if oceanic_data:
                logger.info(f"Oceanic data fetched for praia {praia_id}")
        except Exception as e:
            logger.warning(f"Could not fetch oceanic data: {e}")
        
        # Build forecast response
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
        }
        
        # Add atmospheric data if available
        if atmospheric_data and 'dados' in atmospheric_data:
            forecast['atmospheric'] = atmospheric_data['dados']
        
        # Add oceanic data if available
        if oceanic_data and 'dados' in oceanic_data:
            forecast['oceanic'] = oceanic_data['dados']
        
        logger.info(f"LEGACY_FORECAST_SUCCESS: praia_id={praia_id}")
        return success(forecast)
        
    except Exception as e:
        logger.error(f"LEGACY_FORECAST_ERROR: {str(e)}")
        return server_error(f"Failed to fetch forecast: {str(e)}")
