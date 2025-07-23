from langchain.agents import initialize_agent, AgentType, Tool, AgentExecutor
from langchain_openai import AzureChatOpenAI, OpenAI
from langchain.memory import ConversationBufferMemory
from app.answer import get_rag_chain
from app.tools import get_current_weather, get_weather_forecast, calculate_expression
import logging
import os

logger = logging.getLogger(__name__)

async def create_agent() -> AgentExecutor:
    """Create and configure a LangChain agent with RAG and enhanced tool capabilities."""
    try:
        debug = os.getenv("DEBUG", "false").lower() == "true"
        environment = os.getenv("ENVIRONMENT", "development")
        langchain_tracing_v2 = os.getenv("LANGCHAIN_TRACING_V2", "true").lower() == "true"
        langchain_api_key = os.getenv("LANGCHAIN_API_KEY")
        langchain_project = os.getenv("LANGCHAIN_PROJECT", "wiki-chat-agent")
        logger.info(f"LangChain project: {langchain_project}")
        # Check if LangSmith is enabled
        langsmith_enabled = langchain_tracing_v2 and bool(langchain_api_key)
        
        
        # Initialize LLM with proper configuration from environment variables
        llm = AzureChatOpenAI(
            deployment_name=os.getenv("AZURE_DEPLOYMENT"),
            openai_api_version=os.getenv("OPENAI_API_VERSION"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            openai_api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            temperature=0,
        )
        
        # Get the RAG chain
        rag_chain = await get_rag_chain()
        
        # Define tools for the agent
        tools = [
            Tool(
                name="wikipedia_search",
                func=rag_chain.invoke,
                description="Search Wikipedia knowledge base for information about any topic. Use this when you need factual information, historical data, or general knowledge about people, places, events, concepts, etc."
            ),
            Tool(
                name="weather_current",
                func=get_current_weather,
                description="Get current weather information for any city or location. Use this when users ask about current weather conditions. Input should be just the city name (e.g., 'London', 'New York', 'Tokyo')."
            ),
            Tool(
                name="weather_forecast",
                func=get_weather_forecast,
                description="Get weather forecast for any city. Use this when users ask about future weather or weather predictions. Input format: 'location' for 3-day forecast or 'location, days' for specific number of days (1-5). Example: 'London, 5' for 5-day forecast."
            ),
            Tool(
                name="calculator",
                func=calculate_expression,
                description="Perform basic mathematical calculations. Supports: addition (+), subtraction (-), multiplication (*), division (/), power (**), modulo (%), sqrt(), abs(), round(), and constants pi and e. Use for simple arithmetic like '2+2', 'sqrt(16)', '10*5-3', etc."
            )
        ]

        # Initialize conversation memory
        memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        # Prepare agent kwargs
        agent_kwargs = {
            "system_message": """You are a helpful AI assistant with access to multiple tools:

1. **Wikipedia Search**: For factual information, historical data, and general knowledge
2. **Weather Tools**: For current weather conditions and forecasts
3. **Basic Calculator**: For simple mathematical calculations

When users ask questions:
- Use Wikipedia search for factual information, definitions, history, etc.
- Use weather tools when asked about weather conditions or forecasts
- Use calculator for basic math problems (arithmetic, sqrt, percentages, etc.)
- You can use multiple tools if needed to provide comprehensive answers
- Always provide helpful, accurate, and well-formatted responses

Be conversational and helpful. If you're not sure which tool to use, try the most relevant one first."""
        }
        
        # Add LangSmith-specific tags if enabled
        if langsmith_enabled:
            logger.info("Creating agent with LangSmith tracing enabled")
        
        # Create the agent with enhanced capabilities
        agent = initialize_agent(
            tools=tools,
            llm=llm,
            agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
            verbose=debug,
            memory=memory,
            handle_parsing_errors=True,
            max_iterations=3,
            agent_kwargs=agent_kwargs
        )
        
        # Set agent metadata for LangSmith
        if hasattr(agent, 'agent') and hasattr(agent.agent, 'llm_chain'):
            agent.agent.llm_chain.llm.metadata = {
                "environment": environment,
                "agent_type": "wiki_chat_agent",
                "tools": ["wikipedia_search", "weather_current", "weather_forecast", "calculator"]
            }
        
        logger.info("Agent created successfully with Wikipedia, Weather, and Basic Calculator tools")
        
        if langsmith_enabled:
            logger.info(f"Agent traces will be logged to LangSmith project: {langchain_project}")
        
        return agent
        
    except Exception as e:
        logger.error(f"Failed to create agent: {e}")
        raise

