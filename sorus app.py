import os
import json
import streamlit as st
from pathlib import Path
from datetime import datetime
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate

# ============================================================================
# CONFIG & SETUP
# ============================================================================

st.set_page_config(
    page_title="Sorus AI",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ChatGPT-style dark theme CSS
st.markdown("""
<style>
    * {
        color: #ececec;
    }
    
    body, .stApp {
        background-color: #0d0d0d;
        color: #ececec;
    }
    
    .stSidebar {
        background-color: #0d0d0d;
        border-right: 1px solid #2a2a2a;
    }
    
    [data-testid="stMainBlockContainer"] {
        padding-left: 1rem;
        padding-right: 1rem;
    }
    
    .stButton > button {
        background-color: #10a37f !important;
        color: white !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 8px 16px !important;
        font-weight: 500 !important;
        transition: all 0.2s ease;
    }
    
    .stButton > button:hover {
        background-color: #0d9370 !important;
    }
    
    .stTextArea textarea, .stTextInput input {
        background-color: #343541 !important;
        color: #ececec !important;
        border: 1px solid #565869 !important;
        border-radius: 6px !important;
    }
    
    .stTextArea textarea::placeholder, .stTextInput input::placeholder {
        color: #8e8ea0;
    }
    
    h1, h2, h3, h4, h5, h6 {
        color: #ececec;
    }
    
    .chat-container {
        display: flex;
        flex-direction: column;
        gap: 1rem;
    }
    
    .user-message {
        background: transparent;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 6px;
        text-align: right;
    }
    
    .user-text {
        background-color: #10a37f;
        padding: 0.75rem 1rem;
        border-radius: 6px;
        display: inline-block;
        max-width: 80%;
        text-align: left;
    }
    
    .assistant-message {
        background: transparent;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 6px;
        text-align: left;
    }
    
    .assistant-text {
        padding: 0.75rem 1rem;
        border-radius: 6px;
        display: inline-block;
        max-width: 90%;
    }
    
    .sidebar-history {
        background-color: #2a2a2a;
        padding: 10px;
        margin: 8px 0;
        border-radius: 6px;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    
    .sidebar-history:hover {
        background-color: #3a3a3a;
    }
    
    .input-container {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background-color: #0d0d0d;
        border-top: 1px solid #2a2a2a;
        padding: 1rem;
        z-index: 100;
    }
    
    .task-modal {
        background-color: #343541;
        border: 1px solid #565869;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .task-button {
        background-color: #2a2a2a !important;
        color: #ececec !important;
        border: 1px solid #565869 !important;
        border-radius: 6px !important;
        padding: 10px 16px !important;
        margin: 8px !important;
        text-align: left !important;
        transition: all 0.2s ease;
    }
    
    .task-button:hover {
        background-color: #3a3a3a !important;
        border-color: #10a37f !important;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# CONSTANTS & SYSTEM PROMPT
# ============================================================================

SYSTEM_PROMPT = """You are Sorus AI, an expert coding assistant with deep knowledge of software engineering, algorithms, best practices, and multiple programming paradigms.

Your role:
- Provide clear, production-ready solutions
- Include comprehensive explanations
- Generate clean, well-commented code
- Handle edge cases properly
- Offer practical examples

Guidelines:
- Be concise but thorough
- Format code with proper syntax highlighting
- Always consider performance and readability
- Provide step-by-step guidance
- Suggest improvements and alternatives
- Use real-world examples when helpful"""

TASK_TYPES = {
    "🚀 Build": "Generate new code from requirements",
    "🐛 Debug": "Fix and identify bugs in code",
    "🧪 Test": "Generate test cases",
    "⚡ Optimize": "Improve performance and efficiency",
    "📖 Explain": "Understand code line-by-line",
    "💡 Ask": "General programming questions"
}

# ============================================================================
# INIT LLM
# ============================================================================

GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", os.getenv("GROQ_API_KEY"))

if not GROQ_API_KEY:
    st.error("❌ Please set GROQ_API_KEY")
    st.stop()

llm = ChatGroq(
    model="openai/gpt-oss-20b",
    temperature=0.7,
    api_key=GROQ_API_KEY
)

Path("conversations").mkdir(exist_ok=True)
Path("generated_code").mkdir(exist_ok=True)

# ============================================================================
# UTILITY FUNCTIONS (DEFINED FIRST)
# ============================================================================

def generate_chat_id():
    """Generate unique chat ID"""
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def save_conversation():
    """Save current conversation to disk"""
    if st.session_state.current_chat_id:
        chat_file = f"conversations/{st.session_state.current_chat_id}.json"
        with open(chat_file, "w") as f:
            json.dump(st.session_state.chat_messages, f)

def load_conversations():
    """Load all saved conversations"""
    convs = {}
    if Path("conversations").exists():
        for file in Path("conversations").glob("*.json"):
            try:
                with open(file) as f:
                    messages = json.load(f)
                    if messages:
                        chat_id = file.stem
                        preview = messages[0].get("content", "")[:40]
                        convs[chat_id] = preview
            except:
                pass
    st.session_state.conversations = convs

def delete_conversation(chat_id):
    """Delete a conversation"""
    chat_file = f"conversations/{chat_id}.json"
    if Path(chat_file).exists():
        Path(chat_file).unlink()
    st.session_state.conversations.pop(chat_id, None)
    if st.session_state.current_chat_id == chat_id:
        st.session_state.current_chat_id = None
        st.session_state.chat_messages = []
    st.rerun()

def start_new_chat():
    """Start a new conversation"""
    save_conversation()
    st.session_state.current_chat_id = generate_chat_id()
    st.session_state.chat_messages = []
    st.rerun()

def load_chat(chat_id):
    """Load a specific conversation"""
    save_conversation()
    st.session_state.current_chat_id = chat_id
    chat_file = f"conversations/{chat_id}.json"
    try:
        with open(chat_file) as f:
            st.session_state.chat_messages = json.load(f)
    except:
        st.session_state.chat_messages = []
    st.rerun()

def build_prompt(task_type, user_input, code_context=""):
    """Build contextualized prompt based on task type"""
    
    prompts = {
        "🚀 Build": f"""Generate production-ready code based on this requirement:

{user_input}

MUST INCLUDE:
- All necessary imports
- Comprehensive comments explaining logic
- Full error handling
- Clear variable names
- Type hints where applicable
- Usage example
- Edge case handling

Return ONLY complete code with no explanations.""",

        "🐛 Debug": f"""Find and fix bugs in this code:

{code_context}

Issue description: {user_input}

Provide:
1. **Bugs found** - List each bug with location
2. **Fixes applied** - How you fixed them
3. **Fixed code** - Complete corrected code

Return the fixed code at the end.""",

        "🧪 Test": f"""Generate comprehensive test cases for this code:

{code_context}

Testing focus: {user_input}

Include:
- Normal case tests
- Edge cases (empty, null, zero, negative)
- Error handling tests
- Clear comments
- Ready to run

Return ONLY complete test code.""",

        "⚡ Optimize": f"""Optimize this code for: {user_input}

Code to optimize:
{code_context}

Provide:
1. **Analysis** - Performance bottlenecks identified
2. **Optimizations** - Specific improvements
3. **Optimized code** - Complete refactored code

Return the optimized code at the end.""",

        "📖 Explain": f"""Explain this code line-by-line:

{code_context}

Focus on: {user_input}

Format each section:
**Lines X-Y:**
[show the code]

**What it does:** Clear explanation
**Why it matters:** Context and significance

Be thorough for all logic.""",

        "💡 Ask": f"""Answer this programming question:

{user_input}

Include:
1. **Direct Answer** - Clear response
2. **Explanation** - Why this is correct
3. **Code Example** - If applicable
4. **Best Practices** - Tips and tricks
5. **Common Mistakes** - What to avoid"""
    }
    
    return prompts.get(task_type, user_input)

def stream_response(placeholder, prompt):
    """Stream response from LLM"""
    try:
        prompt_obj = PromptTemplate.from_template(prompt)
        chain = prompt_obj | llm
        full_response = ""
        
        for chunk in chain.stream({}):
            if hasattr(chunk, 'content'):
                full_response += chunk.content
            else:
                full_response += str(chunk)
            placeholder.markdown(full_response + "▌")
        
        placeholder.markdown(full_response)
        return full_response
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        return f"Error: {str(e)}"

def save_code(filename, code):
    """Save generated code to file"""
    path = f"generated_code/{filename}.txt"
    with open(path, "w") as f:
        f.write(code)
    st.success(f"✅ Saved: {path}")
    return path

# ============================================================================
# SESSION STATE
# ============================================================================

if "conversations" not in st.session_state:
    st.session_state.conversations = {}
    load_conversations()

if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None

if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

# ============================================================================
# SIDEBAR - CONVERSATION HISTORY
# ============================================================================

with st.sidebar:
    st.title("⚡ Sorus AI")
    st.markdown("---")
    
    # New Chat Button
    if st.button("➕ New Chat", use_container_width=True):
        start_new_chat()
    
    st.markdown("---")
    st.subheader("💬 Chat History")
    
    # Load conversations
    load_conversations()
    
    if st.session_state.conversations:
        for chat_id, preview in sorted(st.session_state.conversations.items(), reverse=True):
            col1, col2 = st.columns([4, 1])
            with col1:
                if st.button(f"📌 {preview}", key=f"load_{chat_id}", use_container_width=True):
                    load_chat(chat_id)
            with col2:
                if st.button("🗑️", key=f"del_{chat_id}"):
                    delete_conversation(chat_id)
    else:
        st.info("💡 No conversations yet. Start with ➕ New Chat!")
    
    st.markdown("---")
    st.markdown("**Note:** Always review AI-generated code before using in production!")

# ============================================================================
# MAIN CHAT INTERFACE
# ============================================================================

st.title("⚡ Sorus AI - Coding Assistant")
st.markdown("---")

# Start new chat if none selected
if st.session_state.current_chat_id is None:
    st.info("👈 Start a new chat or load one from history!")
    st.stop()

# Display chat history
if st.session_state.chat_messages:
    for msg in st.session_state.chat_messages:
        role = msg["role"]
        content = msg["content"]
        
        if role == "user":
            st.markdown(f"""
            <div class='chat-message user'>
                <strong>You:</strong><br>
                {content}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class='chat-message assistant'>
                <strong>⚡ Sorus AI:</strong><br>
                {content}
            </div>
            """, unsafe_allow_html=True)

st.markdown("---")

# Input Section
col1, col2 = st.columns([4, 2])

with col1:
    user_input = st.text_area(
        "Your message:",
        placeholder="Type your request...",
        height=80,
        key="user_input"
    )

with col2:
    st.write("")
    task_type = st.selectbox(
        "Task:",
        list(TASK_TYPES.keys()),
        key="task_type",
        label_visibility="collapsed"
    )

# Code context (for code-related tasks)
if task_type in ["🐛 Debug", "🧪 Test", "⚡ Optimize", "📖 Explain"]:
    code_input = st.text_area(
        "Paste your code:",
        placeholder="Your code here...",
        height=120,
        key="code_input"
    )
else:
    code_input = ""

# Action buttons
col1, col2, col3 = st.columns([2, 2, 2])

with col1:
    if st.button("🚀 Send", use_container_width=True):
        if not user_input.strip():
            st.error("❌ Please enter a message!")
            st.stop()
        
        # Build the prompt
        full_prompt = build_prompt(task_type, user_input, code_input)
        
        # Add to chat history
        st.session_state.chat_messages.append({
            "role": "user",
            "content": user_input
        })
        
        # Get response
        with st.spinner("⏳ Generating response..."):
            placeholder = st.empty()
            response = stream_response(placeholder, full_prompt)
        
        # Save response
        st.session_state.chat_messages.append({
            "role": "assistant",
            "content": response
        })
        
        # Save conversation
        save_conversation()
        st.rerun()

with col2:
    if st.button("💾 Save Code", use_container_width=True):
        if code_input.strip():
            filename = st.text_input("Filename:", value="code_output", key="save_fname")
            if filename:
                save_code(filename, code_input)
        else:
            st.warning("⚠️ No code to save!")

with col3:
    if st.button("🗑️ Clear Chat", use_container_width=True):
        if st.session_state.current_chat_id:
            delete_conversation(st.session_state.current_chat_id)
            start_new_chat()

st.markdown("---")
st.markdown("""
<div style='text-align: center; padding: 20px; color: #999;'>
    <p>⚡ <strong>Sorus AI</strong> - Your Coding Assistant</p>
    <p>Always review AI-generated code before using in production!</p>
</div>
""", unsafe_allow_html=True)
