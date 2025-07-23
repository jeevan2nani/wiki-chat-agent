import streamlit as st
import requests
import uuid
import time
from typing import Dict, Any

# Page configuration
st.set_page_config(
    page_title="Wiki-Powered Chatbot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .user-message {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
    }
    .bot-message {
        background-color: #f3e5f5;
        border-left: 4px solid #9c27b0;
    }
    .error-message {
        background-color: #ffebee;
        border-left: 4px solid #f44336;
        color: #c62828;
    }
    .tools-info {
        background-color: #e8f5e8;
        padding: 8px;
        margin: 8px 0;
        border-radius: 4px;
        border-left: 3px solid #4caf50;
        font-size: 0.9em;
        line-height: 1.4;
    }
    .tool-input {
        color: #666;
        font-style: italic;
        margin-left: 20px;
    }
</style>
""", unsafe_allow_html=True)

# App title and description
st.title("🌐 Wiki-Powered Chatbot 🤖")
st.markdown("### Ask me anything! I'll search Wikipedia to give you accurate answers.")
st.markdown("---")

# Sidebar configuration
with st.sidebar:
    st.header("🔧 Configuration")
    
    # Backend URL configuration
    backend_host = st.text_input(
        "Backend Host", 
        value="http://backend:8000",
        help="URL of the backend API"
    )
    
    # Model settings
    st.subheader("⚙️ Settings")
    show_session_id = st.checkbox("Show Session ID", value=False)
    max_history_length = st.slider("Max Chat History", 5, 50, 20)
    
    # Clear session button
    if st.button("🗑️ Clear Chat History"):
        st.session_state.chat_history = []
        st.rerun()

# Initialize session state
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
    
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
    
if "is_loading" not in st.session_state:
    st.session_state.is_loading = False

# Display session ID if requested
if show_session_id:
    st.info(f"Session ID: `{st.session_state.session_id}`")

# Chat interface
def send_message(message: str) -> Dict[str, Any]:
    """Send message to backend and return response."""
    try:
        response = requests.post(
            f"{backend_host}/chat",
            json={
                "session_id": st.session_state.session_id, 
                "message": message
            },
            timeout=30  # 30 second timeout
        )
        
        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        else:
            return {
                "success": False, 
                "error": f"Server error: {response.status_code} - {response.text}"
            }
            
    except requests.exceptions.Timeout:
        return {"success": False, "error": "Request timed out. Please try again."}
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "Cannot connect to backend. Is the server running?"}
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": f"Request failed: {str(e)}"}
    except Exception as e:
        return {"success": False, "error": f"Unexpected error: {str(e)}"}

# Chat input
col1, col2 = st.columns([4, 1])

with col1:
    user_input = st.text_input(
        "Ask me something:", 
        key="user_input",
        disabled=st.session_state.is_loading,
        placeholder="e.g., What is quantum computing?"
    )

with col2:
    send_button = st.button(
        "Send 📤", 
        disabled=st.session_state.is_loading or not user_input.strip()
    )

# Handle message sending
if send_button and user_input.strip():
    # Add user message to history
    st.session_state.chat_history.append({
        "role": "user", 
        "content": user_input.strip(),
        "timestamp": time.time()
    })
    
    # Show loading state
    st.session_state.is_loading = True
    
    with st.spinner("🤔 Thinking and searching Wikipedia..."):
        # Send request to backend
        result = send_message(user_input.strip())
        
        if result["success"]:
            bot_reply = result["data"].get("response", "No response received")
            tools_used = result["data"].get("tools_used", [])
            st.session_state.chat_history.append({
                "role": "bot", 
                "content": bot_reply,
                "tools_used": tools_used,
                "timestamp": time.time()
            })
        else:
            # Add error message to chat
            st.session_state.chat_history.append({
                "role": "error", 
                "content": f"Error: {result['error']}",
                "timestamp": time.time()
            })
    
    # Reset loading state
    st.session_state.is_loading = False
    
    # Clear input and rerun to update UI
    st.rerun()

# Display chat history
if st.session_state.chat_history:
    st.markdown("### 💬 Chat History")
    
    # Show only recent messages based on max_history_length
    recent_messages = st.session_state.chat_history[-max_history_length:]
    
    for i, msg in enumerate(recent_messages):
        if msg["role"] == "user":
            st.markdown(f"""
            <div class="chat-message user-message">
                <strong>👤 You:</strong><br>
                {msg['content']}
            </div>
            """, unsafe_allow_html=True)
            
        elif msg["role"] == "bot":
            # Display bot message
            st.markdown(f"""
            <div class="chat-message bot-message">
                <strong>🤖 Bot:</strong><br>
                {msg['content']}
            </div>
            """, unsafe_allow_html=True)
            
            # Display tools used separately if they exist
            if msg.get("tools_used"):
                with st.expander("🔍 Tools Used", expanded=True):
                    for tool in msg["tools_used"]:
                        tool_name = tool.get("name", "Unknown")
                        tool_input = tool.get("input", "")
                        
                        # Add appropriate emojis for different tools
                        if "wikipedia" in tool_name.lower():
                            icon = "📚"
                        elif "weather" in tool_name.lower():
                            icon = "🌤️"
                        elif "calculator" in tool_name.lower():
                            icon = "🧮"
                        else:
                            icon = "🔧"
                        
                        st.write(f"{icon} **{tool_name}**")
                        if tool_input:
                            st.caption(f"└─ Input: `{tool_input}`")
            
        elif msg["role"] == "error":
            st.markdown(f"""
            <div class="chat-message error-message">
                <strong>❌ Error:</strong><br>
                {msg['content']}
            </div>
            """, unsafe_allow_html=True)

# Footer with stats and info
if st.session_state.chat_history:
    total_messages = len([m for m in st.session_state.chat_history if m["role"] in ["user", "bot"]])
    st.markdown("---")
    st.caption(f"💬 Total conversation turns: {total_messages // 2}")

# Health check section
with st.expander("🔍 Backend Status"):
    if st.button("Check Backend Health"):
        try:
            health_response = requests.get(f"{backend_host}/health", timeout=5)
            if health_response.status_code == 200:
                health_data = health_response.json()
                st.success("✅ Backend is healthy!")
                st.json(health_data)
            else:
                st.error(f"❌ Backend returned status: {health_response.status_code}")
        except Exception as e:
            st.error(f"❌ Cannot reach backend: {str(e)}")

# LangSmith Observability status
with st.expander("📊 LangSmith Observability"):
    if st.button("Check Observability Status"):
        try:
            obs_response = requests.get(f"{backend_host}/observability/status", timeout=5)
            if obs_response.status_code == 200:
                obs_data = obs_response.json()
                if obs_data.get("langsmith_enabled"):
                    st.success("✅ LangSmith tracing is enabled!")
                    st.info(f"**Project:** {obs_data.get('project')}")
                    st.info(f"**Endpoint:** {obs_data.get('endpoint')}")
                    st.caption("All agent interactions are being traced and monitored.")
                else:
                    st.warning("⚠️ LangSmith tracing is disabled")
                    st.caption("Set LANGCHAIN_API_KEY to enable observability.")
                st.json(obs_data)
            else:
                st.error(f"❌ Could not get observability status: {obs_response.status_code}")
        except Exception as e:
            st.error(f"❌ Cannot check observability status: {str(e)}")

# Example queries section
with st.expander("💡 Example Questions"):
    st.markdown("""
    **✨ New Feature: Tool Visibility**
    Now you can see exactly which tools the AI used to answer your questions!
    Each response will show which tools were triggered and what inputs were used.
    
    **📚 Wikipedia Knowledge:**
    - What is artificial intelligence?
    - Tell me about the history of computers
    - Who was Albert Einstein?
    - Explain quantum physics
    
    **🌤️ Weather Information:**
    - What's the weather like in London?
    - Show me the 5-day forecast for Tokyo
    - Is it raining in New York right now?
    
    **🧮 Basic Calculations:**
    - Calculate 15% of 250: 250 * 0.15
    - What is the square root of 144?
    - Calculate 2 + 3 * 4
    - Find 2 to the power of 8: 2**8
    
    **🤝 Combined Questions:**
    - What's the weather in Paris and calculate 20°C in Fahrenheit: 20 * 9/5 + 32
    - Tell me about the Pythagorean theorem and calculate: sqrt(3**2 + 4**2)
    
    **🔍 Tool Information:**
    Watch for the green "Tools Used" section that appears below each AI response to see:
    - 📚 Wikipedia searches with search terms
    - 🌤️ Weather queries with location details  
    - 🧮 Calculator operations with expressions
    """)

# Loading indicator
if st.session_state.is_loading:
    st.info("🔄 Processing your request...")
