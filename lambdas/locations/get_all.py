"""
Get all locations endpoint
GET /locations
"""

import json
import logging
from common.db import execute_query
from common.responses import success, server_error

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    Get all locations in hierarchical format
    """
    try:
        logger.info("Fetching all locations")
        
        # Query all locations
        sql = """
            SELECT * FROM locais 
            WHERE nivel IN (1, 2, 3, 4) 
            ORDER BY nivel, nome
        """
        locations = execute_query(sql)
        
        # Query all beaches - removed ativa filter
        sql_beaches = """
            SELECT p.*, l.nome as localidade_nome 
            FROM praias p 
            LEFT JOIN locais l ON p.local_id = l.id 
            ORDER BY p.nome
        """
        beaches = execute_query(sql_beaches)
        
        # Build hierarchical tree
        location_tree = build_location_tree(locations, beaches)
        
        logger.info(f"Returning {len(location_tree)} root locations")
        return success(location_tree)
        
    except Exception as e:
        logger.error(f"Error fetching locations: {e}")
        return server_error(f"Failed to fetch locations: {str(e)}")


def build_location_tree(locations, beaches):
    """
    Build hierarchical location tree with beaches
    """
    location_map = {loc['id']: convert_location(loc) for loc in locations}
    
    # Group beaches by municipality
    beaches_by_municipality = {}
    for beach in beaches:
        municipio_id = beach['local_id']
        if municipio_id not in beaches_by_municipality:
            beaches_by_municipality[municipio_id] = []
        beaches_by_municipality[municipio_id].append(beach)
    
    # Attach beaches to municipalities
    for loc in locations:
        node = location_map.get(loc['id'])
        if not node:
            continue
            
        # Beaches are children of municipalities (nivel 4)
        if loc['nivel'] == 4 and loc['id'] in beaches_by_municipality:
            municipio_beaches = beaches_by_municipality[loc['id']]
            node['children'] = [
                convert_beach(beach, loc['id']) 
                for beach in municipio_beaches
            ]
    
    # Build parent-child relationships
    roots = []
    for loc in locations:
        node = location_map.get(loc['id'])
        if not node:
            continue
            
        if node['parentId']:
            parent = location_map.get(node['parentId'])
            if parent:
                if 'children' not in parent:
                    parent['children'] = []
                parent['children'].append(node)
        elif loc['nivel'] == 1:  # Continents are roots
            roots.append(node)
    
    return roots


def convert_location(loc):
    """Convert database location to API format"""
    return {
        'id': loc['id'],
        'type': 'REGULAR_SPOT',
        'name': loc.get('nome', loc.get('name', '')),
        'parentId': loc.get('pai'),
        'coastId': loc.get('litoral_id'),
        'coordinates': {
            'lat': loc['lat'],
            'long': loc['lon']
        } if loc.get('lat') and loc.get('lon') else None,
        'children': []
    }


def convert_beach(praia, parent_id):
    """Convert database beach to API format"""
    return {
        'id': praia['id'],
        'type': 'SURF_SPOT',
        'name': praia.get('nome_2', praia.get('nome', f"Praia {praia['nome']}")),
        'parentId': parent_id,
        'coastId': praia.get('litoral_id'),
        'spotId': praia['id'],
        'oceanicSpotId': praia.get('litoral_id'),
        'coordinates': {
            'lat': praia['lat'],
            'long': praia['lon']
        } if praia.get('lat') and praia.get('lon') else None,
        'children': []
    }
