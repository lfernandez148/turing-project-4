"""ChromaDB configuration module."""
import os
from loguru import logger
import chromadb
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ChromaDB connection settings
CHROMA_HOST = os.getenv("CHROMA_SERVER_HOST", "localhost")
CHROMA_PORT = os.getenv("CHROMA_SERVER_HTTP_PORT", "8030")


def get_chroma_client():
    """Get a configured ChromaDB client for the containerized instance."""
    logger.info(f"Connecting to ChromaDB at {CHROMA_HOST}:{CHROMA_PORT}")
    
    try:
        # Initialize client for containerized ChromaDB
        client = chromadb.HttpClient(
            host=CHROMA_HOST,
            port=CHROMA_PORT,
            ssl=False
        )
        
        logger.info("Successfully connected to ChromaDB")
        return client
        
    except Exception as e:
        logger.error(f"Failed to connect to ChromaDB: {e}")
        raise


def get_or_create_collection(client, name="campaign_reports"):
    """Get or create a ChromaDB collection with the specified name."""
    try:
        collection = client.get_or_create_collection(
            name=name,
            metadata={"hnsw:space": "cosine"}
        )
        logger.info(f"Successfully got/created collection: {name}")
        return collection
        
    except Exception as e:
        logger.error(f"Failed to get/create collection {name}: {e}")
        raise