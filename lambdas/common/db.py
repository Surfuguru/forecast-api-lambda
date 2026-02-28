"""
Database connection pooling for Lambda functions
"""

import pymysql
import os
import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Global connection
_connection = None


def get_connection():
    """Get or create database connection"""
    global _connection
    
    if _connection is None:
        logger.info("Creating new database connection")
        
        _connection = pymysql.connect(
            host=os.environ['FORECAST_API_MYSQL_HOST'],
            user=os.environ['FORECAST_API_MYSQL_USER'],
            password=os.environ['FORECAST_API_MYSQL_PASSWORD'],
            database=os.environ['FORECAST_API_MYSQL_DATABASE'],
            connect_timeout=5,
            read_timeout=10,
            write_timeout=10,
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True
        )
        
        logger.info("Database connection created")
    
    return _connection


def execute_query(sql: str, params: tuple = None) -> List[Dict[str, Any]]:
    """Execute query and return results"""
    global _connection
    
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            
            if cursor.description:
                results = cursor.fetchall()
                return results if results is not None else []
            else:
                return [{'affected_rows': cursor.rowcount}]
                
    except pymysql.Error as e:
        logger.error(f"Database error: {e}")
        _connection = None
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise


def close_connection():
    """Close database connection"""
    global _connection
    
    if _connection:
        _connection.close()
        _connection = None
        logger.info("Database connection closed")
