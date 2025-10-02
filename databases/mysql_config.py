"""MySQL configuration module."""
import os
from loguru import logger
import mysql.connector
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MySQL connection settings
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
MYSQL_USER = os.getenv("MYSQL_USER", "appuser")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "apppassword")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "appdb")


def get_mysql_client():
    """Get a configured MySQL client for the containerized instance."""
    logger.info(f"Connecting to MySQL at {MYSQL_HOST}:{MYSQL_PORT}")
    
    try:
        # Initialize connection to MySQL
        connection = mysql.connector.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE
        )
        
        logger.info("Successfully connected to MySQL")
        return connection
        
    except Exception as e:
        logger.error(f"Failed to connect to MySQL: {e}")
        raise
