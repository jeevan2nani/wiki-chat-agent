# 🤖 Wiki-Powered Chat Agent with Tool Visibility ✨

A sophisticated AI chatbot powered by Wikipedia knowledge, live weather data, and mathematical calculations with complete tool usage transparency. Built with FastAPI, Streamlit, LangChain, and ChromaDB.

## 🆕 New Feature: Tool Visibility
See exactly which tools the AI uses for each response:
- 📚 **Wikipedia searches** with search terms used
- 🌤️ **Weather queries** with location details  
- 🧮 **Calculator operations** with expressions evaluated

Each response now shows a "🔍 Tools Used" section displaying which tools were triggered and their inputs!

## ✨ Features

### 🧠 **Core Capabilities**
- **Wikipedia Knowledge Search**: RAG-powered search through Wikipedia data
- **Live Weather Information**: Current conditions and 5-day forecasts
- **Basic Calculator**: Safe evaluation of simple mathematical expressions
- **Tool Transparency**: See which tools are triggered for each response
- **Conversation Memory**: Maintains context across the session
- **Multi-tool Intelligence**: Combines tools to answer complex questions
- **LangSmith Observability**: Complete tracing and monitoring of agent interactions

### 🛠️ **Tools Available**

#### 📚 **Wikipedia Search**
- Search through indexed Wikipedia articles
- Provides factual information, historical data, and general knowledge
- Uses vector similarity search for relevant results

#### 🌤️ **Weather Tools**
- **Current Weather**: Real-time weather conditions for any city
- **Weather Forecast**: 1-5 day forecasts with detailed information
- Powered by OpenWeatherMap API

#### 🧮 **Basic Calculator**
- **Basic Operations**: +, -, *, /, **, %
- **Simple Functions**: sqrt(), abs(), round(), pow()
- **Constants**: π (pi), e
- **Safe Evaluation**: Uses AST parsing to prevent code injection

#### 📊 **LangSmith Observability**
- **Complete Tracing**: Every agent interaction is tracked and logged
- **Performance Monitoring**: Track response times and success rates
- **Debugging Support**: Detailed trace information for troubleshooting
- **Session Tracking**: Monitor conversations across user sessions
- **Tool Usage Analytics**: See which tools are used most frequently

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- **Azure OpenAI API** credentials
- OpenWeather API key
- LangSmith API key (optional - for observability and debugging)

### Environment Setup

1. **Set Environment Variables**:
```bash
# Required - Azure OpenAI Configuration
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
export AZURE_OPENAI_API_KEY="your-azure-openai-api-key"
export AZURE_DEPLOYMENT="your-model-deployment-name"
export OPENAI_API_VERSION="2025-01-01-preview"

# Optional but recommended
export OPENWEATHER_API_KEY="your-openweather-api-key"
export LANGCHAIN_API_KEY="ls_your-langsmith-api-key"
export LANGCHAIN_PROJECT="wiki-chat-agent"
export LANGCHAIN_TRACING_V2="true"
```

**Or create a `.env` file in the project root:**
```bash
# .env file

# Required - Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-azure-openai-api-key
AZURE_DEPLOYMENT=your-model-deployment-name
OPENAI_API_VERSION=2025-01-01-preview

# Optional - Weather API
OPENWEATHER_API_KEY=your-openweather-api-key

# Optional - LangSmith Observability
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=ls_your-langsmith-api-key
LANGCHAIN_PROJECT=wiki-chat-agent

# Optional - Application Settings
LOG_LEVEL=INFO
ENVIRONMENT=development
```

2. **Run with Docker Compose**:
```bash
docker-compose up --build
```

3. **Access the Application**:
- **Frontend (Streamlit)**: http://localhost:8501
- **Backend API**: http://localhost:8000  
- **API Documentation**: http://localhost:8000/docs
- **ChromaDB**: http://localhost:8001

## 💬 Usage Examples

### Wikipedia Knowledge
```
User: "Tell me about quantum computing"
Agent: [Searches Wikipedia and provides detailed information about quantum computing principles, history, and applications]

🔍 Tools Used:
📚 wikipedia_search
└─ Input: quantum computing
```

### Weather Information  
```
User: "What's the weather like in Tokyo?"
Agent: 🌤️ Current Weather for Tokyo, JP:
🌡️ Temperature: 18°C (feels like 17°C)
☁️ Conditions: Clear Sky
💧 Humidity: 60%
...

🔍 Tools Used:
🌤️ weather_current
└─ Input: Tokyo
```

### Basic Calculations
```
User: "Calculate the area of a circle with radius 5"
Agent: The result of calculating pi * 5**2 is 78.5398

🔍 Tools Used:
🧮 calculator
└─ Input: pi * 5**2
```


```

## 🏗️ Architecture

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit     │────│    FastAPI      │────│    ChromaDB     │
│   Frontend      │    │    Backend      │    │  Vector Store   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ├── LangChain Agent
                                ├── Wikipedia Tool (RAG)
                                ├── Weather Tool (API)
                                └── Calculator Tool (AST)

```
### Local Development

1. **Install Dependencies**:
```bash
cd app && pip install -r requirements.txt
cd ../frontend && pip install -r requirements.txt
```

2. **Run Components**:
```bash
# Terminal 1: ChromaDB
docker run -p 8001:8000 chromadb/chroma

# Terminal 2: Backend
cd app && uvicorn main:app --reload --port 8000

# Terminal 3: Frontend  
cd frontend && streamlit run gui.py --server.port 8501
```