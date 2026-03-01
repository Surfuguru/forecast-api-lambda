"""
Legacy forecast endpoint - Full version with S3 integration and parsed output
GET /forecast?praia_id={id}

Returns forecast in SurfForecastResponse format matching the /surf-forecast API
"""

import json
import logging
import boto3
import os
from botocore.exceptions import ClientError
from common.db import execute_query
from common.responses import success, bad_request, not_found, server_error
from parser.builder import ForecastBuilder

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
    
    Returns parsed forecast in SurfForecastResponse format:
    {
        "id": "123",
        "date": "2026-03-01",
        "type": "SURF",
        "name": "Maracaípe",
        "orientation": 92,
        "forecast": {
            "maxHeight": 1.5,
            "maxEnergy": 120,
            "maxPower": 15.8,
            "maxWind": 25,
            "days": [...]
        }
    }
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
                pr.nome_do_mapa as nome_do_mapa,
                pr.dt_mapa_atualizado as dt_mapa_atualizado,
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
        
        # Validate we have required data
        if not oceanic_data or not oceanic_data.get('dados'):
            return not_found(f'Forecast data not found for beach {praia_id}')
        
        # Build parsed forecast response
        try:
            forecast = ForecastBuilder.build_forecast(
                beach_data=beach,
                forecast_type='SURF',
                atmospheric_data=atmospheric_data,
                oceanic_data=oceanic_data
            )
            
            logger.info(f"LEGACY_FORECAST_SUCCESS: praia_id={praia_id}, days={len(forecast.get('forecast', {}).get('days', []))}")
            return success(forecast)
            
        except Exception as parse_error:
            logger.error(f"Failed to parse forecast: {parse_error}")
            return server_error(f"Failed to parse forecast data: {str(parse_error)}")
        
    except Exception as e:
        logger.error(f"LEGACY_FORECAST_ERROR: {str(e)}")
        return server_error(f"Failed to fetch forecast: {str(e)}")
