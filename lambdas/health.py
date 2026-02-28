"""
Health check endpoint
GET /health
"""

import json
from common.responses import success

def lambda_handler(event, context):
    """
    Health check - no authentication required
    """
    return success({
        'application': 'wave-prediction-service',
        'message': 'OK',
        'region': context.invoked_function_arn.split(':')[3]
    })
