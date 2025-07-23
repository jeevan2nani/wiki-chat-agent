import os
from langchain_chroma import Chroma
from langchain_openai import AzureChatOpenAI
from langchain.chains.retrieval_qa.base import RetrievalQA
import chromadb
import logging
from langchain.embeddings import HuggingFaceEmbeddings

logger = logging.getLogger(__name__)

# Environment variables with defaults
CHROMA_HOST = os.getenv("CHROMA_HOST", "localhost")
CHROMA_PORT = os.getenv("CHROMA_PORT", "8001")
CHROMA_URL = f"http://{CHROMA_HOST}:{CHROMA_PORT}"
CHROMA_COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "wiki_collection")

def get_chroma_client():
    """Get ChromaDB client with proper configuration."""
    try:
        
        hf_embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        
        # Create ChromaDB HTTP client
        chroma_client = chromadb.HttpClient(
            host=CHROMA_HOST,
            port=int(CHROMA_PORT)
        )
        
        vectorstore = Chroma(
            client=chroma_client,
            collection_name=CHROMA_COLLECTION_NAME, 
            embedding_function=hf_embeddings
        )
        
        logger.info(f"Connected to ChromaDB at {CHROMA_URL}")
        return vectorstore
        
    except Exception as e:
        logger.error(f"Failed to connect to ChromaDB: {e}")
        raise

async def get_rag_chain():
    """Create RAG chain with proper error handling."""
    try:
        # Get configuration from environment variables
        openai_model = os.getenv("AZURE_OPENAI_MODEL", "gpt-4o")
        openai_temperature = float(os.getenv("OPENAI_TEMPERATURE", "0.1"))
        openai_max_tokens = int(os.getenv("OPENAI_MAX_TOKENS", "100000"))
        retrieval_k = int(os.getenv("RETRIEVAL_K", "5"))  # Number of documents to retrieve
        
        # Initialize embeddings and vector store
        vectorstore = get_chroma_client()
        retriever = vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": retrieval_k}  # Return top k most similar documents
        )
        
        # Initialize LLM with environment-based configuration
        llm = AzureChatOpenAI(
            deployment_name=os.getenv("AZURE_DEPLOYMENT"),
            openai_api_version=os.getenv("OPENAI_API_VERSION"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            openai_api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            temperature=0,
        )
        
        # Create RAG chain
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm, 
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=True,
            verbose=True
        )
        
        logger.info(f"RAG chain created successfully with model: {openai_model}, temperature: {openai_temperature}, retrieval_k: {retrieval_k}")
        return qa_chain
        
    except Exception as e:
        logger.error(f"Failed to create RAG chain: {e}")
        raise