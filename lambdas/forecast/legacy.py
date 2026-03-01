"""
Legacy forecast endpoint - Full version with S3 integration and parsed output
GET /forecast?praia_id={id}  - For SURF_SPOTs (surf spots with beach data)
GET /forecast?coastId={id}   - For REGULAR_SPOTs (regional locations with atmospheric data only)

Returns forecast in SurfForecastResponse format matching the /surf-forecast API
"""

import json
import logging
import boto3
import os
from botocore.exceptions import ClientError
from common.db import execute_query
from common.responses import success, bad_request, not_found, server_error
from forecast.parser.builder import ForecastBuilder

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
    
    Supports two modes:
    1. praia_id - Surf spot with full beach/oceanic data
    2. coastId - Regional location with atmospheric data only
    
    Returns parsed forecast in SurfForecastResponse format
    """
    try:
        logger.info("LEGACY_FORECAST_REQUEST")
        
        # Parse parameters
        params = event.get('queryStringParameters', {}) or {}
        praia_id = params.get('praia_id')
        coast_id = params.get('coastId')
        
        # Validate - need either praia_id or coastId
        if not praia_id and not coast_id:
            return bad_request('Missing required parameter: praia_id or coastId')
        
        bucket = os.environ.get('FORECAST_API_AWS_FORECAST_BUCKET', 'previsao')
        
        # Mode 1: Surf spot (praia_id)
        if praia_id:
            return handle_surf_spot_forecast(praia_id, bucket)
        
        # Mode 2: Regional location (coastId)
        return handle_regional_forecast(coast_id, bucket)
        
    except Exception as e:
        logger.error(f"LEGACY_FORECAST_ERROR: {str(e)}")
        return server_error(f"Failed to fetch forecast: {str(e)}")


def handle_surf_spot_forecast(praia_id, bucket):
    """Handle forecast for surf spots with full beach/oceanic data"""
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
    
    logger.info(f"SURF_SPOT_RESOLVED: praia_id={praia_id}, litoral_id={litoral_id}")
    
    # Fetch atmospheric data from S3
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
        
        logger.info(f"SURF_FORECAST_SUCCESS: praia_id={praia_id}, days={len(forecast.get('forecast', {}).get('days', []))}")
        return success(forecast)
        
    except Exception as parse_error:
        logger.error(f"Failed to parse forecast: {parse_error}")
        return server_error(f"Failed to parse forecast data: {str(parse_error)}")


def handle_regional_forecast(coast_id, bucket):
    """Handle forecast for regional locations with atmospheric data only"""
    # Get location data from locais table using litoral_id (coastId)
    sql = """
        SELECT 
            lo.id,
            lo.nome,
            lo.litoral_id,
            lo.lat,
            lo.lon,
            (SELECT lo2.sigla FROM locais lo2 WHERE lo2.id = lo.pai) as uf
        FROM locais lo
        WHERE lo.litoral_id = %s
        LIMIT 1
    """
    
    result = execute_query(sql, (coast_id,))
    
    if not result:
        return not_found(f'Location with coastId {coast_id} not found')
    
    location = result[0]
    litoral_id = coast_id  # coastId is the litoral_id
    
    logger.info(f"REGIONAL_SPOT_RESOLVED: coastId={coast_id}, name={location['nome']}")
    
    # Fetch atmospheric data from S3
    atmos_key = f"atmos/atmos{litoral_id}pro.json"
    atmospheric_data = None
    try:
        atmospheric_data = fetch_s3_object(bucket, atmos_key)
        if atmospheric_data:
            logger.info(f"Atmospheric data fetched for litoral {litoral_id}")
    except Exception as e:
        logger.warning(f"Could not fetch atmospheric data: {e}")
    
    # For regional forecasts, use oceanic data from the coast (oceano file)
    # This provides general wave conditions for the region
    oceanic_key = f"oceanos/oceano{litoral_id}.json"
    oceanic_data = None
    try:
        oceanic_data = fetch_s3_object(bucket, oceanic_key)
        if oceanic_data:
            logger.info(f"Oceanic data fetched for coast {litoral_id}")
    except Exception as e:
        logger.warning(f"Could not fetch oceanic data: {e}")
    
    # Validate we have atmospheric data at minimum
    if not atmospheric_data or not atmospheric_data.get('dados'):
        return not_found(f'Atmospheric data not found for coast {coast_id}')
    
    # Build beach_data dict for the builder
    beach_data = {
        'praia_id': location['id'],
        'id': location['id'],
        'nome': location['nome'],
        'orientacao': None,  # No orientation for regional spots
    }
    
    # Build parsed forecast response
    try:
        forecast = ForecastBuilder.build_forecast(
            beach_data=beach_data,
            forecast_type='OCEANIC',  # Use OCEANIC type for regional forecasts
            atmospheric_data=atmospheric_data,
            oceanic_data=oceanic_data
        )
        
        logger.info(f"REGIONAL_FORECAST_SUCCESS: coastId={coast_id}, days={len(forecast.get('forecast', {}).get('days', []))}")
        return success(forecast)
        
    except Exception as parse_error:
        logger.error(f"Failed to parse regional forecast: {parse_error}")
        return server_error(f"Failed to parse forecast data: {str(parse_error)}")
