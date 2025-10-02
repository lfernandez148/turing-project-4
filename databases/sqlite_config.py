# databases/sqlite_config.py
"""
SQLite database configuration and setup.
Centralized configuration and initialization for all SQLite databases.
"""

import sqlite3
import pandas as pd
from pathlib import Path
from loguru import logger

# Base directories
DATABASES_DIR = Path(__file__).parent
SQLITE_DIR = DATABASES_DIR / "sqlite"
DATA_DIR = Path(__file__).parent.parent / "data"
CSV_DIR = DATA_DIR / "csv"

# Ensure directories exist
SQLITE_DIR.mkdir(exist_ok=True)
CSV_DIR.mkdir(parents=True, exist_ok=True)


class SQLiteConfig:
    """SQLite database configuration and setup."""
    
    # Database paths
    CAMPAIGNS_DB = SQLITE_DIR / "campaigns.db"
    CONVERSATIONS_DB = SQLITE_DIR / "conversations.db"
    CAMPAIGN_CSV = CSV_DIR / "campaign_data.csv"
    
    @classmethod
    def setup_databases(cls):
        """Initialize all SQLite databases."""
        logger.info("=== Setting up SQLite databases ===")
        success = True
        
        # Setup campaigns database
        logger.info("📊 Setting up campaigns database...")
        try:
            cls.setup_campaigns_db()
            logger.success("✅ Campaigns database ready")
        except Exception as e:
            logger.error(f"❌ Campaigns database setup failed: {e}")
            success = False
            
        # Setup conversations database
        logger.info("💬 Setting up conversations database...")
        try:
            cls.setup_conversations_db()
            logger.success("✅ Conversations database ready")
        except Exception as e:
            logger.error(f"❌ Conversations database setup failed: {e}")
            success = False
            
        return success
    
    @classmethod
    def setup_campaigns_db(cls):
        """Setup campaigns database and load initial data."""
        # Read CSV data
        df = pd.read_csv(cls.CAMPAIGN_CSV)
        logger.info(f"Loaded {len(df)} campaigns from CSV")
        
        # Create database and load data
        conn = sqlite3.connect(cls.CAMPAIGNS_DB)
        df.to_sql('campaigns', conn, if_exists='replace', index=False)
        
        # Create indexes for better performance
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_campaign_id
            ON campaigns(campaign_id)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_campaign_topic
            ON campaigns(campaign_topic)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_customer_segment
            ON campaigns(customer_segment)
        """)
        conn.close()
        
    @classmethod
    def setup_conversations_db(cls):
        """Setup conversations database schema."""
        conn = sqlite3.connect(cls.CONVERSATIONS_DB)
        
        # Create conversations tracking table
        conn.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id TEXT UNIQUE NOT NULL,
            total_tokens INTEGER DEFAULT 0,
            prompt_tokens INTEGER DEFAULT 0,
            completion_tokens INTEGER DEFAULT 0,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Create indexes
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_conversation_id
            ON conversations(conversation_id)
        """)
        conn.close()
    
    @classmethod
    def get_campaigns_db(cls) -> str:
        """Get campaigns database path."""
        return str(cls.CAMPAIGNS_DB)
    
    @classmethod
    def get_conversations_db(cls) -> str:
        """Get conversations database path."""
        return str(cls.CONVERSATIONS_DB)
    
    @classmethod
    def get_campaign_csv(cls) -> str:
        """Get campaign CSV data path."""
        return str(cls.CAMPAIGN_CSV)
    
    @classmethod
    def get_database_connection(cls, db_path: str) -> sqlite3.Connection:
        """Get a database connection for the specified database."""
        return sqlite3.connect(db_path)
