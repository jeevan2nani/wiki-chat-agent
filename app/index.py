from datasets import load_dataset
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain.schema import Document
from app.answer import get_chroma_client
import logging
import os

logger = logging.getLogger(__name__)

def generate_embeddings(docs):
    """Generate embeddings for documents."""
    try:
        embeddings = OpenAIEmbeddings()
        return embeddings.embed_documents(docs)
    except Exception as e:
        logger.error(f"Error generating embeddings: {e}")
        raise

def index_data():
    """Index Wikipedia dataset into ChromaDB."""
    try:
        
        # Get configuration from environment variables
        batch_size = int(os.getenv("BATCH_SIZE", "5"))
        max_documents = int(os.getenv("MAX_DOCUMENTS", "5"))
        chunk_size = int(os.getenv("CHUNK_SIZE", "1000"))
        chunk_overlap = int(os.getenv("CHUNK_OVERLAP", "200"))
        
        logger.info("Starting data indexing process...")
        logger.info(f"Configuration: batch_size={batch_size}, max_documents={max_documents}, chunk_size={chunk_size}, chunk_overlap={chunk_overlap}")
        
        # Load Wikipedia dataset (smaller subset for faster processing)
        logger.info("Loading Wikipedia dataset...")
        wiki_dataset = load_dataset(
            "wikipedia", 
            "20220301.en", 
            split="train", 
            streaming=True
        )
        
        # Initialize text splitter
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size, 
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        # Get vector store
        vectorstore = get_chroma_client()
        
        docs = []
        processed_count = 0
        
        for i, page in enumerate(wiki_dataset):
            if processed_count >= max_documents:
                break
                
            try:
                logger.info(f"Processing page {i + 1}: {page.get('title', 'Unknown')}")
                
                # Skip pages with no text
                text = page.get("text", "")
                if not text or len(text.strip()) < 100:
                    continue
                
                # Split text into chunks
                splits = text_splitter.split_text(text)
                
                # Create Document objects with metadata
                for j, split in enumerate(splits):
                    if len(split.strip()) < 50:  # Skip very short chunks
                        continue
                        
                    doc = Document(
                        page_content=split,
                        metadata={
                            "source": page.get("title", "Unknown"),
                            "page_id": page.get("id", f"page_{i}"),
                            "chunk_id": f"chunk_{j}",
                            "url": page.get("url", "")
                        }
                    )
                    docs.append(doc)
                
                # Process in batches
                if len(docs) >= batch_size:
                    logger.info(f"Adding batch of {len(docs)} documents to vector store...")
                    vectorstore.add_documents(docs)
                    processed_count += len(docs)
                    docs = []  # Clear the batch
                    logger.info(f"Total documents processed: {processed_count}")
                    
            except Exception as e:
                logger.error(f"Error processing page {i}: {e}")
                continue
        
        # Add any remaining documents
        if docs:
            logger.info(f"Adding final batch of {len(docs)} documents...")
            vectorstore.add_documents(docs)
            processed_count += len(docs)
        
        logger.info(f"Data indexing completed successfully! Total documents indexed: {processed_count}")
        
    except Exception as e:
        logger.error(f"Error during data indexing: {e}")
        raise

if __name__ == "__main__":
    # Configure logging for standalone execution
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger.info("Starting data indexing process...")
    index_data()
