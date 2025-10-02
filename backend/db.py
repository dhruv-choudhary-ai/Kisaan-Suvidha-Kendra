import psycopg2
import sqlite3
import os
from config import Config
import logging

logger = logging.getLogger(__name__)

def get_db_connection():
    """
    Get database connection based on DB_TYPE in config
    Supports PostgreSQL and SQLite (for testing)
    """
    db_type = getattr(Config, 'DB_TYPE', 'postgresql')
    
    if db_type == 'sqlite':
        # SQLite connection for testing
        db_path = getattr(Config, 'SQLITE_DB_PATH', 'kisaan_assist.db')
        logger.info(f"Connecting to SQLite database: {db_path}")
        
        conn = sqlite3.connect(db_path)
        # Enable foreign keys in SQLite
        conn.execute("PRAGMA foreign_keys = ON")
        # Return dict-like rows
        conn.row_factory = sqlite3.Row
        return conn
    else:
        # PostgreSQL connection
        logger.info(f"Connecting to PostgreSQL database: {Config.DB_NAME}")
        return psycopg2.connect(
            dbname=Config.DB_NAME,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            host=Config.DB_HOST,
            port=Config.DB_PORT
        )
