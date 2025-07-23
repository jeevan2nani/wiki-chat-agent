import subprocess
import asyncio
import logging
from pathlib import Path
from app.answer import get_chroma_client

logger = logging.getLogger(__name__)

async def check_and_index():
    """Check if ChromaDB has documents and run indexing if needed."""
    logger.info("Checking if ChromaDB has indexed documents...")
    
    try:
        # Connect to ChromaDB
        db = get_chroma_client()
        
        # Check document count
        count = db._collection.count()
        logger.info(f"Found {count} documents in ChromaDB.")
        
        if count == 0:
            logger.info("No documents found. Running ingestion...")
            await run_ingestion()
        else:
            logger.info("ChromaDB already populated. Skipping ingestion.")
            
    except Exception as e:
        logger.error(f"Error during startup check: {e}")
        logger.warning("Application will start without pre-indexed data")

async def run_ingestion():
    """Run the data ingestion process."""
    try:
        logger.info("Starting data ingestion directly...")
        from app.index import index_data
        await asyncio.to_thread(index_data)  # Run in thread so it doesn’t block event loop
        logger.info("Data ingestion completed successfully")
    except Exception as e:
        logger.error(f"Error running ingestion: {e}")
        raise

