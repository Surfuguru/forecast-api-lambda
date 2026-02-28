"""
Standard API response formatting
"""

import json
from typing import Any, Dict, Optional

def response(
    status_code: int = 200,
    body: Any = None,
    headers: Optional[Dict] = None
) -> Dict:
    """
    Create standard API Gateway response
    """
    default_headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization'
    }
    
    if headers:
        default_headers.update(headers)
    
    return {
        'statusCode': status_code,
        'headers': default_headers,
        'body': json.dumps(body) if body is not None else ''
    }


def success(body: Any) -> Dict:
    """200 OK response"""
    return response(200, body)


def created(body: Any) -> Dict:
    """201 Created response"""
    return response(201, body)


def bad_request(message: str) -> Dict:
    """400 Bad Request response"""
    return response(400, {'error': 'BadRequest', 'message': message})


def not_found(message: str = 'Resource not found') -> Dict:
    """404 Not Found response"""
    return response(404, {'error': 'NotFound', 'message': message})


def server_error(message: str = 'Internal server error') -> Dict:
    """500 Internal Server Error response"""
    return response(500, {'error': 'ServerError', 'message': message})
