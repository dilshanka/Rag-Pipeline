import streamlit as st
import requests
import json
from datetime import datetime
import time

# Page configuration
st.set_page_config(
    page_title="🎓 Academic Study Assistant",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global styles */
    .stApp {
        font-family: 'Inter', sans-serif;
    }
    
    /* Main header with modern gradient */
    .main-header {
        text-align: center;
        padding: 3rem 2rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
        color: white;
        border-radius: 20px;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
        position: relative;
        overflow: hidden;
    }
    
    .main-header::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grain" width="100" height="100" patternUnits="userSpaceOnUse"><circle cx="25" cy="25" r="1" fill="white" opacity="0.1"/><circle cx="75" cy="75" r="1" fill="white" opacity="0.1"/><circle cx="50" cy="10" r="0.5" fill="white" opacity="0.1"/><circle cx="10" cy="60" r="0.5" fill="white" opacity="0.1"/><circle cx="90" cy="40" r="0.5" fill="white" opacity="0.1"/></pattern></defs><rect width="100" height="100" fill="url(%23grain)"/></svg>');
        opacity: 0.3;
    }
    
    .main-header h1 {
        font-size: 3rem;
        font-weight: 700;
        margin: 0;
        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
        position: relative;
        z-index: 1;
    }
    
    .main-header p {
        font-size: 1.2rem;
        font-weight: 400;
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
        position: relative;
        z-index: 1;
    }
    
    /* Chat message styling */
    .chat-message {
        padding: 1.5rem;
        border-radius: 20px;
        margin: 1.5rem 0;
        border-left: 5px solid;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        position: relative;
        backdrop-filter: blur(10px);
    }
    
    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        margin-left: 15%;
        border-left-color: #4c63d2;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    
    .user-message::before {
        content: '👤';
        position: absolute;
        left: -2.5rem;
        top: 50%;
        transform: translateY(-50%);
        font-size: 1.5rem;
        background: white;
        border-radius: 50%;
        width: 2rem;
        height: 2rem;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    }
    
    .assistant-message {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        margin-right: 15%;
        border-left-color: #e91e63;
        box-shadow: 0 4px 15px rgba(240, 147, 251, 0.3);
    }
    
    .assistant-message::before {
        content: '🎓';
        position: absolute;
        right: -2.5rem;
        top: 50%;
        transform: translateY(-50%);
        font-size: 1.5rem;
        background: white;
        border-radius: 50%;
        width: 2rem;
        height: 2rem;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    }
    
    /* Status indicators */
    .status-success {
        background: linear-gradient(135deg, #4ade80 0%, #22c55e 100%);
        color: white;
        padding: 1rem;
        border-radius: 15px;
        border: none;
        box-shadow: 0 4px 15px rgba(74, 222, 128, 0.3);
        font-weight: 500;
    }
    
    .status-error {
        background: linear-gradient(135deg, #f87171 0%, #ef4444 100%);
        color: white;
        padding: 1rem;
        border-radius: 15px;
        border: none;
        box-shadow: 0 4px 15px rgba(248, 113, 113, 0.3);
        font-weight: 500;
    }
    
    /* Example questions */
    .example-question {
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
        padding: 1rem 1.5rem;
        border-radius: 15px;
        border: 2px solid transparent;
        cursor: pointer;
        transition: all 0.3s ease;
        font-weight: 500;
        color: #475569;
        margin: 0.5rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    .example-question:hover {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
        border-color: #4c63d2;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background: linear-gradient(180deg, #f8fafc 0%, #e2e8f0 100%);
    }
    
    /* Input styling */
    .stTextInput > div > div > input {
        border-radius: 15px;
        border: 2px solid #e2e8f0;
        padding: 0.75rem 1rem;
        font-size: 1rem;
        transition: all 0.3s ease;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 15px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
    }
    
    /* Chat container */
    .chat-container {
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
        border-radius: 20px;
        padding: 2rem;
        margin: 1rem 0;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    }
    
    /* Footer */
    .footer {
        text-align: center;
        color: #64748b;
        padding: 2rem;
        background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
        border-radius: 15px;
        margin-top: 2rem;
    }
    
    /* Loading animation */
    .loading-dots {
        display: inline-block;
    }
    
    .loading-dots::after {
        content: '';
        animation: dots 1.5s steps(5, end) infinite;
    }
    
    @keyframes dots {
        0%, 20% { content: ''; }
        40% { content: '.'; }
        60% { content: '..'; }
        80%, 100% { content: '...'; }
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .user-message, .assistant-message {
            margin-left: 5%;
            margin-right: 5%;
        }
        
        .user-message::before, .assistant-message::before {
            display: none;
        }
        
        .main-header h1 {
            font-size: 2rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "api_status" not in st.session_state:
    st.session_state.api_status = "unknown"
if "student_name" not in st.session_state:
    st.session_state.student_name = "Student"

# API Configuration
API_BASE_URL = "http://localhost:8000"

def check_api_status():
    """Check if the API is running and healthy"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            st.session_state.api_status = "healthy"
            return True
        else:
            st.session_state.api_status = "unhealthy"
            return False
    except requests.exceptions.RequestException:
        st.session_state.api_status = "offline"
        return False

def send_message(message, student_name):
    """Send message to the API and return response"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/chat",
            json={
                "message": message,
                "student_name": student_name
            },
            timeout=30
        )
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"API Error: {response.status_code}"}
    except requests.exceptions.RequestException as e:
        return {"error": f"Connection Error: {str(e)}"}

# Main header
st.markdown("""
<div class="main-header">
    <h1>🎓 Academic Study Assistant</h1>
    <p>Ask questions about your course materials and get instant help!</p>
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    
    # Student name input
    st.session_state.student_name = st.text_input(
        "Your Name", 
        value=st.session_state.student_name,
        help="This will be used to personalize your experience"
    )
    
    # API Status
    st.header("🔗 Connection Status")
    if st.button("🔄 Check Connection"):
        check_api_status()
    
    if st.session_state.api_status == "healthy":
        st.markdown('<div class="status-success">✅ Connected to Study Assistant</div>', unsafe_allow_html=True)
    elif st.session_state.api_status == "unhealthy":
        st.markdown('<div class="status-error">⚠️ API is running but unhealthy</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="status-error">❌ Cannot connect to Study Assistant</div>', unsafe_allow_html=True)
        st.info("Make sure the API server is running: `python rag_api.py`")
    
    # Database info
    st.header("📚 Your Documents")
    
    # Current documents section
    with st.container():
        st.markdown("### 📖 Current Documents")
        
        # Document card
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown("**Machine Learning Lecture Notes**")
        with col2:
            st.markdown("`2 chunks`")
        
        st.markdown("---")
        
        # Add documents section
        st.markdown("### ➕ Add More Documents")
        
        st.markdown("""
        **To add more course materials:**
        
        1. **Place PDFs** in `university_documents/` folder
        2. **Process documents** by running:
           ```bash
           python chromadbpdf.py
           ```
        3. **Restart** the API server
        
        **Supported formats:**
        - 📄 PDF files (lecture notes, textbooks, papers)
        - 📝 Text files (.txt, .md)
        - 📊 Research papers and assignments
        """)
        
        # Quick stats
        st.markdown("---")
        st.markdown("**📊 Database Stats:**")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Documents", "1")
        with col2:
            st.metric("Chunks", "2")
        with col3:
            st.metric("Size", "0.01 MB")
    
    # Example questions
    st.header("💡 Example Questions")
    example_questions = [
        "What is machine learning?",
        "Can you explain supervised learning?",
        "What are the key concepts in this chapter?",
        "How does reinforcement learning work?",
        "What should I focus on for the exam?",
        "Can you give me an example of classification?"
    ]
    
    for question in example_questions:
        if st.button(f"❓ {question}", key=f"example_{question}"):
            st.session_state.messages.append({"role": "user", "content": question})
            st.rerun()

# Main chat interface
st.markdown("""
<div class="chat-container">
    <h2 style="text-align: center; color: #334155; margin-bottom: 2rem; font-weight: 600;">
        💬 Chat with Your Study Assistant
    </h2>
""", unsafe_allow_html=True)

# Display chat messages
if not st.session_state.messages:
    st.markdown("""
    <div style="text-align: center; padding: 3rem; color: #64748b;">
        <div style="font-size: 4rem; margin-bottom: 1rem;">🎓</div>
        <h3 style="color: #334155; margin-bottom: 1rem;">Welcome to your Study Assistant!</h3>
        <p style="font-size: 1.1rem; line-height: 1.6;">
            I'm here to help you understand your course materials. Ask me anything about machine learning, 
            or try one of the example questions in the sidebar!
        </p>
    </div>
    """, unsafe_allow_html=True)

for message in st.session_state.messages:
    if message["role"] == "user":
        st.markdown(f"""
        <div class="chat-message user-message">
            <strong>You:</strong> {message["content"]}
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="chat-message assistant-message">
            <strong>🎓 Study Assistant:</strong><br>
            {message["content"]}
        </div>
        """, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# Chat input
with st.form("chat_form", clear_on_submit=True):
    col1, col2 = st.columns([4, 1])
    
    with col1:
        user_input = st.text_input(
            "Ask a question about your course materials...",
            placeholder="e.g., What is machine learning?",
            label_visibility="collapsed"
        )
    
    with col2:
        submit_button = st.form_submit_button("Ask", use_container_width=True)

# Process the form submission
if submit_button and user_input:
    if st.session_state.api_status != "healthy":
        st.error("⚠️ Please check your connection to the Study Assistant first!")
        st.stop()
    
    # Add user message to chat
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # Show loading spinner with custom message
    with st.spinner("🤔 Thinking about your question..."):
        # Send message to API
        response = send_message(user_input, st.session_state.student_name)
    
    # Process response
    if "error" in response:
        assistant_message = f"❌ Error: {response['error']}"
    else:
        assistant_message = response.get("response", "No response received")
    
    # Add assistant response to chat
    st.session_state.messages.append({"role": "assistant", "content": assistant_message})
    
    # Rerun to show new messages
    st.rerun()

# Footer
st.markdown("""
<div class="footer">
    <div style="font-size: 2rem; margin-bottom: 1rem;">🎓</div>
    <h4 style="color: #334155; margin-bottom: 0.5rem; font-weight: 600;">Academic Study Assistant</h4>
    <p style="margin-bottom: 0.5rem; font-weight: 500;">Powered by Advanced RAG Technology</p>
    <p style="font-size: 0.9rem; opacity: 0.8;">Add your course materials to get personalized help!</p>
    <div style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid #e2e8f0;">
        <small style="color: #94a3b8;">
            Built with ❤️ for students | Streamlit + LangChain + OpenAI
        </small>
    </div>
</div>
""", unsafe_allow_html=True)

# Auto-check API status on first load
if st.session_state.api_status == "unknown":
    check_api_status()
    st.rerun()
