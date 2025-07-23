from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List
import logging
import os
from app.agent import create_agent
from app.startup import check_and_index
from langchain.agents import AgentExecutor
from langchain.callbacks.base import BaseCallbackHandler
from langchain.schema import AgentAction, AgentFinish

# Custom callback to capture tool usage
class ToolUsageCallback(BaseCallbackHandler):
    def __init__(self):
        self.tools_used = []
    
    def on_agent_action(self, action: AgentAction, **kwargs) -> Any:
        """Called when an agent action is taken."""
        tool_input = getattr(action, 'tool_input', '')
        self.tools_used.append({
            "name": action.tool,
            "input": str(tool_input)[:100] + "..." if len(str(tool_input)) > 100 else str(tool_input)
        })
        logger.info(f"Tool used: {action.tool} with input: {tool_input}")
    
    def reset(self):
        """Reset the tools used list."""
        self.tools_used = []

# Helper functions for setup
def configure_logging():
    """Configure application logging."""
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    debug = os.getenv("DEBUG", "false").lower() == "true"
    
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Set third-party library log levels
    if not debug:
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("chromadb").setLevel(logging.WARNING)
        logging.getLogger("openai").setLevel(logging.WARNING)

def setup_langsmith():
    """Set up LangSmith tracing if configured."""
    langchain_tracing_v2 = os.getenv("LANGCHAIN_TRACING_V2", "true").lower() == "true"
    langchain_api_key = os.getenv("LANGCHAIN_API_KEY")
    langchain_project = os.getenv("LANGCHAIN_PROJECT", "wiki-chat-agent")
    langchain_endpoint = os.getenv("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com")
    
    langsmith_enabled = langchain_tracing_v2 and bool(langchain_api_key)
    
    if langsmith_enabled:
        # Set environment variables for LangChain
        os.environ["LANGCHAIN_TRACING_V2"] = str(langchain_tracing_v2).lower()
        os.environ["LANGCHAIN_API_KEY"] = langchain_api_key
        os.environ["LANGCHAIN_PROJECT"] = langchain_project
        os.environ["LANGCHAIN_ENDPOINT"] = langchain_endpoint
        
        logger.info(f"LangSmith tracing enabled for project: {langchain_project}")
    else:
        logger.info("LangSmith tracing disabled - set LANGCHAIN_API_KEY to enable")
        
    return langsmith_enabled

# Configure logging
configure_logging()
logger = logging.getLogger(__name__)

# Get environment variables for app configuration
api_title = os.getenv("API_TITLE", "Wiki-Powered Chat Agent")
api_version = os.getenv("API_VERSION", "1.0.0")
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:8501,http://frontend:8501").split(",")
environment = os.getenv("ENVIRONMENT", "development")
langchain_project = os.getenv("LANGCHAIN_PROJECT", "wiki-chat-agent")
langchain_endpoint = os.getenv("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com")
langchain_tracing_v2 = os.getenv("LANGCHAIN_TRACING_V2", "true").lower() == "true"
langchain_api_key = os.getenv("LANGCHAIN_API_KEY")
langsmith_enabled = langchain_tracing_v2 and bool(langchain_api_key)

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        # Set up LangSmith tracing
        langsmith_enabled = setup_langsmith()
        
        # Initialize data indexing
        await check_and_index()
        
        logger.info("Application startup completed successfully")
        if langsmith_enabled:
            logger.info("LangSmith observability is active - traces will be sent to LangSmith")
    except Exception as e:
        logger.error(f"Failed to initialize application: {e}")
        raise
    yield
    # Cleanup logic can go here
    logger.info("Application shutting down")

app = FastAPI(
    title=api_title,
    description="A RAG-based chatbot using Wikipedia data with LangSmith observability",
    version=api_version,
    lifespan=lifespan
)

# Add CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Thread-safe session storage (consider Redis for production)
session_agents: Dict[str, AgentExecutor] = {}

class ChatRequest(BaseModel):
    session_id: str
    message: str

class QuestionRequest(BaseModel):
    session_id: str
    question: str

class ChatResponse(BaseModel):
    response: str
    session_id: str
    langsmith_enabled: bool = langsmith_enabled
    tools_used: list = []

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        if request.session_id not in session_agents:
            session_agents[request.session_id] = await create_agent()
            logger.info(f"Created new agent for session: {request.session_id}")
        
        agent: AgentExecutor = session_agents[request.session_id]
        logger.info(f"LangSmith enabled: {langsmith_enabled} for session: {request.session_id} and request: {request.message}")
        # Add metadata for LangSmith tracing
        metadata = {
            "session_id": request.session_id,
            "environment": environment,
            "user_message": request.message[:100] + "..." if len(request.message) > 100 else request.message
        }
        logger.info(f"Metadata: {metadata}")
        # Create callback to capture tool usage
        tool_callback = ToolUsageCallback()
        callbacks = [tool_callback]
        
        # Run the agent with metadata and capture tool usage
        try:
            if langsmith_enabled:
                from langchain.callbacks import LangChainTracer
                tracer = LangChainTracer(
                    project_name=langchain_project,
                    session_name=f"session_{request.session_id}"
                )
                callbacks.append(tracer)
                logger.info(f"Calling agent with LangSmith tracing and tool callback")
            else:
                logger.info(f"Calling agent with tool callback only")
            
            result = await agent.ainvoke(
                {"input": request.message},
                config={"callbacks": callbacks, "tags": ["chat", "wiki-agent"], "metadata": metadata}
            )
            
            # Extract response and tool usage information
            response = result.get("output", "No response generated")
            tools_used = tool_callback.tools_used
            logger.info(f"Tools captured via callback: {len(tools_used)}")
            
        except Exception as e:
            logger.error(f"Error during agent execution: {e}")
            # Fallback to simple arun with callback
            try:
                response = await agent.arun(request.message, callbacks=[tool_callback])
                tools_used = tool_callback.tools_used
            except Exception as fallback_error:
                logger.error(f"Fallback also failed: {fallback_error}")
                response = "I apologize, but I encountered an error processing your request."
                tools_used = []
        
        return ChatResponse(
            response=response, 
            session_id=request.session_id,
            langsmith_enabled=langsmith_enabled,
            tools_used=tools_used
        )
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "sessions": len(session_agents),
        "langsmith_enabled": langsmith_enabled,
        "environment": environment,
        "project": langchain_project if langsmith_enabled else None
    }

# Alternative endpoint for backward compatibility
@app.post("/ask", response_model=ChatResponse)
async def ask(request: QuestionRequest):
    """Alternative endpoint that accepts 'question' field."""
    try:
        chat_request = ChatRequest(session_id=request.session_id, message=request.question)
        return await chat(chat_request)
    except Exception as e:
        logger.error(f"Error in ask endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.delete("/sessions/{session_id}")
async def clear_session(session_id: str):
    if session_id in session_agents:
        del session_agents[session_id]
        logger.info(f"Cleared session: {session_id}")
        return {"message": "Session cleared successfully"}
    raise HTTPException(status_code=404, detail="Session not found")

@app.get("/observability/status")
async def observability_status():
    """Get LangSmith observability status."""
    return {
        "langsmith_enabled": langsmith_enabled,
        "project": langchain_project,
        "endpoint": langchain_endpoint,
        "tracing_v2": langchain_tracing_v2
    }