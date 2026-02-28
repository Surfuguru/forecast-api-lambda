"""
Database connection pooling for Lambda functions
Uses connection pooling to reuse connections across invocations
"""

import pymysql
import os
import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Global connection pool (persists across warm invocations)
_connection = None

def get_connection():
    """
    Get database connection
    Creates new connection if doesn't exist (cold start)
    Reuses connection if exists (warm start)
    """
    global _connection
    
    if _connection is None:
        logger.info("Creating new database connection")
        
        _connection = pymysql.connect(
            host=os.environ['FORECAST_API_MYSQL_HOST'],
            user=os.environ['FORECAST_API_MYSQL_USER'],
            password=os.environ['FORECAST_API_MYSQL_PASSWORD'],
            database=os.environ['FORECAST_API_MYSQL_DATABASE'],
            connect_timeout=10,
            read_timeout=30,
            write_timeout=30,
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True
        )
        
        logger.info("Database connection created")
    
    return _connection


def execute_query(sql: str, params: tuple = None) -> List[Dict[str, Any]]:
    """
    Execute a query and return results
    Handles connection management automatically
    """
    global _connection
    
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            
            if cursor.description:  # SELECT query
                return cursor.fetchall()
            else:  # INSERT/UPDATE/DELETE
                return [{'affected_rows': cursor.rowcount}]
                
    except pymysql.Error as e:
        logger.error(f"Database error: {e}")
        # Reset connection on error
        _connection = None
        raise
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise


def close_connection():
    """Close connection (call on Lambda shutdown)"""
    global _connection
    
    if _connection:
        _connection.close()
        _connection = None
        logger.info("Database connection closed")
