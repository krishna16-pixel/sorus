import os
import sys
from pathlib import Path
import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
import time

# ==================== PAGE CONFIG ====================
st.set_page_config(
    page_title="🚀 Coding Education Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== CUSTOM CSS ====================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;600&family=Inter:wght@300;400;600;700&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    /* Smooth transitions */
    .stMarkdown, .stCode, .stButton {
        animation: fadeIn 0.3s ease-in;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Main container */
    .main {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    
    /* Code blocks */
    .stCode {
        background-color: #1e1e1e;
        border-radius: 10px;
        padding: 15px;
        font-family: 'Fira Code', monospace;
    }
    
    /* Chat messages */
    .chat-message {
        padding: 12px 16px;
        border-radius: 10px;
        margin: 10px 0;
        animation: slideIn 0.3s ease-out;
    }
    
    @keyframes slideIn {
        from { opacity: 0; transform: translateX(-20px); }
        to { opacity: 1; transform: translateX(0); }
    }
    
    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 15px;
        padding: 12px 16px;
        margin-left: auto;
        max-width: 70%;
        word-wrap: break-word;
    }
    
    .assistant-message {
        background: white;
        color: #333;
        border-radius: 15px;
        padding: 12px 16px;
        margin-right: auto;
        max-width: 70%;
        border-left: 4px solid #667eea;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 20px rgba(102, 126, 234, 0.4);
    }
    
    /* Error/Warning boxes */
    .error-box {
        background: #fee;
        border-left: 4px solid #f44;
        padding: 12px 16px;
        border-radius: 8px;
        margin: 10px 0;
    }
    
    .success-box {
        background: #efe;
        border-left: 4px solid #4f4;
        padding: 12px 16px;
        border-radius: 8px;
        margin: 10px 0;
    }
    
    .warning-box {
        background: #ffe;
        border-left: 4px solid #fa0;
        padding: 12px 16px;
        border-radius: 8px;
        margin: 10px 0;
    }
    
    /* Expandable sections */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%);
        border-radius: 8px;
    }
    
    /* Input styling */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        border-radius: 8px;
        border: 2px solid #667eea;
        background-color: white;
    }
    
    /* Metrics */
    .metric-card {
        background: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# ==================== SETUP ====================
API_KEY = st.secrets.get("GOOGLE_API_KEY", os.getenv("GOOGLE_API_KEY"))

if not API_KEY:
    st.error("❌ Please set your GOOGLE_API_KEY in .streamlit/secrets.toml or environment variables")
    st.stop()

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.3, api_key=API_KEY)
Path("generated_code").mkdir(exist_ok=True)

# Initialize session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "generated_files" not in st.session_state:
    st.session_state.generated_files = []

# ==================== SAVE CODE ====================
def save_code(filename, code, language):
    ext = {"python": "py", "javascript": "js", "java": "java", "cpp": "cpp"}.get(language, "txt")
    path = f"generated_code/{filename}.{ext}"
    with open(path, "w") as f:
        f.write(code)
    st.session_state.generated_files.append({"name": filename, "path": path, "code": code})
    return path

# ==================== DETECT INTENT ====================
def detect_intent(text):
    text = text.lower()
    
    if any(w in text for w in ["build", "create", "generate", "write", "make"]):
        return "build"
    elif any(w in text for w in ["debug", "fix", "error", "wrong"]):
        return "debug"
    elif any(w in text for w in ["test", "testing"]):
        return "test"
    elif any(w in text for w in ["improve", "optimize", "better", "faster"]):
        return "optimize"
    elif any(w in text for w in ["explain", "understand", "teach", "learn", "what is"]):
        return "explain"
    elif any(w in text for w in ["how", "find", "search", "help", "solution"]):
        return "search"
    else:
        return "general"

# ==================== STREAMING CHAIN FUNCTION ====================
def run_chain_stream(template, variables):
    """Run chain with streaming response"""
    prompt = PromptTemplate(template=template, input_variables=list(variables.keys()))
    chain = prompt | llm
    
    # Use streaming with Gemini
    response = ""
    with st.spinner("🔄 Generating response..."):
        for chunk in chain.stream(variables):
            if hasattr(chunk, 'content'):
                response += chunk.content
            else:
                response += str(chunk)
            yield response

def run_chain(template, variables):
    """Run chain normally without streaming (for backend processing)"""
    prompt = PromptTemplate(template=template, input_variables=list(variables.keys()))
    chain = prompt | llm
    response = chain.invoke(variables)
    return response.content if hasattr(response, 'content') else str(response)

# ==================== HANDLERS ====================

def handle_build(user_input):
    st.subheader("🏗️ Build - Code Generation")
    
    # Ask for requirements first
    with st.form("build_form"):
        req = st.text_area(
            "📝 What do you want to build?",
            value=user_input.replace("build", "").replace("create", "").replace("generate", "").strip(),
            height=100,
            placeholder="e.g., Create a Python function to calculate fibonacci numbers"
        )
        
        col1, col2, col3 = st.columns(3)
        with col1:
            language = st.selectbox("Programming Language", ["python", "javascript", "java", "cpp", "c"])
        with col2:
            memory = st.text_input("Memory Limit", "512MB")
        with col3:
            time_limit = st.text_input("Time Limit", "30s")
        
        dependencies = st.text_input("Dependencies (comma-separated)", "")
        
        submitted = st.form_submit_button("🚀 Generate Code", use_container_width=True)
    
    if submitted and req:
        st.session_state.chat_history.append(("user", req))
        
        # Generate code
        st.info("⚙️ Generating code...")
        code_placeholder = st.empty()
        full_response = ""
        
        for partial_response in run_chain_stream("Create working {lang} code for: {req}\n\nReturn ONLY code without explanations.", 
                                                 {"lang": language, "req": req}):
            full_response = partial_response
            code_placeholder.code(full_response, language=language)
        
        st.session_state.chat_history.append(("assistant", full_response))
        
        # Save code
        if st.button("💾 Save Code"):
            filename = req[:30].replace(" ", "_")
            path = save_code(filename, full_response, language)
            st.success(f"✅ Code saved to: `{path}`")
        
        # Show possible outcomes and errors
        st.markdown("---")
        st.subheader("📊 Possible Outcomes & Error Analysis")
        
        outcomes_placeholder = st.empty()
        outcomes_text = ""
        
        for chunk in run_chain_stream(
            "For this {lang} code:\n{code}\n\nWith resources: Memory={mem}, Time={time}, Dependencies={dep}\n\nList:\n1. Possible outputs\n2. Possible errors\n3. Edge cases",
            {"lang": language, "code": full_response, "mem": memory, "time": time_limit, "dep": dependencies or "None"}
        ):
            outcomes_text = chunk
            outcomes_placeholder.markdown(outcomes_text)
        
        st.markdown("---")
        st.subheader("💡 5-Year-Old Explanation")
        
        explanation_placeholder = st.empty()
        explanation_text = ""
        
        for chunk in run_chain_stream(
            "Explain this {lang} code like you're talking to a 5-year-old child. Use very simple words and real-world examples:\n\n{code}",
            {"lang": language, "code": full_response}
        ):
            explanation_text = chunk
            explanation_placeholder.markdown(explanation_text)

def handle_explain(user_input):
    st.subheader("📚 Explain - Learn Concepts")
    
    with st.form("explain_form"):
        topic = st.text_input(
            "What do you want to understand?",
            value=user_input.replace("explain", "").replace("understand", "").strip(),
            placeholder="e.g., recursion, loops, functions, decorators"
        )
        submitted = st.form_submit_button("📖 Explain", use_container_width=True)
    
    if submitted and topic:
        st.session_state.chat_history.append(("user", f"Explain: {topic}"))
        
        # Explanation
        st.markdown("### 🎓 Explanation (For Beginners)")
        explanation_placeholder = st.empty()
        explanation = ""
        
        for chunk in run_chain_stream(
            "Explain '{topic}' for complete beginners learning to code. Use simple words, real-world examples, and maybe an analogy. Include a simple code example.",
            {"topic": topic}
        ):
            explanation = chunk
            explanation_placeholder.markdown(explanation)
        
        st.session_state.chat_history.append(("assistant", explanation))
        
        st.markdown("---")
        
        # Common Mistakes
        st.markdown("### ⚠️ Common Mistakes Beginners Make")
        mistakes_placeholder = st.empty()
        mistakes = ""
        
        for chunk in run_chain_stream(
            "List 3-5 common mistakes beginners make with '{topic}' and how to avoid them. Be brief and clear.",
            {"topic": topic}
        ):
            mistakes = chunk
            mistakes_placeholder.markdown(mistakes)
        
        # Tips
        st.markdown("---")
        st.markdown("### 💡 Pro Tips")
        tips_placeholder = st.empty()
        tips = ""
        
        for chunk in run_chain_stream(
            "Give 3 pro tips for mastering '{topic}'. Keep it concise.",
            {"topic": topic}
        ):
            tips = chunk
            tips_placeholder.markdown(tips)

def handle_debug(user_input):
    st.subheader("🐛 Debug - Fix Your Code")
    
    with st.form("debug_form"):
        col1, col2 = st.columns(2)
        with col1:
            language = st.selectbox("Programming Language", ["python", "javascript", "java", "cpp", "c"], key="debug_lang")
        with col2:
            pass
        
        code = st.text_area("📝 Paste your code:", height=150, placeholder="def my_function():\n pass")
        error = st.text_area("❌ Paste the error message:", height=100, placeholder="Traceback or error output")
        
        submitted = st.form_submit_button("🔧 Fix Code", use_container_width=True)
    
    if submitted and code and error:
        st.session_state.chat_history.append(("user", f"Debug: {code[:100]}..."))
        
        st.markdown("### ✅ Fixed Code")
        fixed_placeholder = st.empty()
        fixed = ""
        
        for chunk in run_chain_stream(
            "Fix this {lang} code that has an error:\n\nCode:\n{code}\n\nError:\n{err}\n\nShow ONLY the corrected code without explanation.",
            {"lang": language, "code": code, "err": error}
        ):
            fixed = chunk
            fixed_placeholder.code(fixed, language=language)
        
        st.session_state.chat_history.append(("assistant", fixed))
        
        st.markdown("---")
        st.markdown("### 📝 Explanation of the Fix")
        explanation_placeholder = st.empty()
        explanation = ""
        
        for chunk in run_chain_stream(
            "Briefly explain what was wrong and how the fix solves it. Keep it simple.",
            {"code": fixed, "err": error}
        ):
            explanation = chunk
            explanation_placeholder.markdown(explanation)

def handle_test(user_input):
    st.subheader("✅ Test - Generate Test Cases")
    
    with st.form("test_form"):
        language = st.selectbox("Programming Language", ["python", "javascript", "java", "cpp", "c"], key="test_lang")
        code = st.text_area("📝 Paste your code:", height=150, placeholder="def add(a, b):\n return a + b")
        
        submitted = st.form_submit_button("🧪 Generate Tests", use_container_width=True)
    
    if submitted and code:
        st.session_state.chat_history.append(("user", f"Test: {code[:100]}..."))
        
        st.markdown("### 🧪 Test Cases")
        test_placeholder = st.empty()
        tests = ""
        
        for chunk in run_chain_stream(
            "Create comprehensive test cases for this {lang} code:\n\n{code}\n\nReturn ONLY test code without explanation.",
            {"lang": language, "code": code}
        ):
            tests = chunk
            test_placeholder.code(tests, language=language)
        
        st.session_state.chat_history.append(("assistant", tests))
        
        st.markdown("---")
        st.markdown("### 📖 Test Explanation")
        explanation_placeholder = st.empty()
        explanation = ""
        
        for chunk in run_chain_stream(
            "Explain what each test case does and why it's important for this function.",
            {"code": code}
        ):
            explanation = chunk
            explanation_placeholder.markdown(explanation)

def handle_optimize(user_input):
    st.subheader("⚡ Optimize - Improve Your Code")
    
    with st.form("optimize_form"):
        language = st.selectbox("Programming Language", ["python", "javascript", "java", "cpp", "c"], key="opt_lang")
        code = st.text_area("📝 Paste your code:", height=150, placeholder="# Your code here")
        
        submitted = st.form_submit_button("🚀 Optimize", use_container_width=True)
    
    if submitted and code:
        st.session_state.chat_history.append(("user", f"Optimize: {code[:100]}..."))
        
        st.markdown("### ⚡ Optimized Code")
        optimized_placeholder = st.empty()
        optimized = ""
        
        for chunk in run_chain_stream(
            "Improve this {lang} code for better performance, readability, and efficiency:\n\n{code}\n\nShow only the optimized code.",
            {"lang": language, "code": code}
        ):
            optimized = chunk
            optimized_placeholder.code(optimized, language=language)
        
        st.session_state.chat_history.append(("assistant", optimized))
        
        st.markdown("---")
        st.markdown("### 📊 Improvements Made")
        improvements_placeholder = st.empty()
        improvements = ""
        
        for chunk in run_chain_stream(
            "List the key improvements made to this code and why they make it better.",
            {"code": optimized}
        ):
            improvements = chunk
            improvements_placeholder.markdown(improvements)

def handle_search(user_input):
    st.subheader("🔍 Search - How-To Solutions")
    
    with st.form("search_form"):
        problem = st.text_area(
            "What do you want to learn how to do?",
            value=user_input.replace("how", "").replace("help", "").replace("search", "").strip(),
            height=80,
            placeholder="e.g., How to read a file in Python, How to create a web server"
        )
        
        submitted = st.form_submit_button("🔎 Search", use_container_width=True)
    
    if submitted and problem:
        st.session_state.chat_history.append(("user", f"How to: {problem}"))
        
        st.markdown("### 📋 Step-by-Step Solution")
        solution_placeholder = st.empty()
        solution = ""
        
        for chunk in run_chain_stream(
            "How to: {prob}\n\nGive a clear step-by-step solution with working code examples.",
            {"prob": problem}
        ):
            solution = chunk
            solution_placeholder.markdown(solution)
        
        st.session_state.chat_history.append(("assistant", solution))

def handle_general(user_input):
    st.subheader("💬 General Question")
    
    with st.form("general_form"):
        question = st.text_area("Your question:", value=user_input, height=100)
        submitted = st.form_submit_button("🤔 Ask", use_container_width=True)
    
    if submitted and question:
        st.session_state.chat_history.append(("user", question))
        
        answer_placeholder = st.empty()
        answer = ""
        
        for chunk in run_chain_stream(
            "Answer this programming question clearly and helpfully:\n\n{q}",
            {"q": question}
        ):
            answer = chunk
            answer_placeholder.markdown(answer)
        
        st.session_state.chat_history.append(("assistant", answer))

# ==================== SIDEBAR ====================
with st.sidebar:
    st.markdown("## 🚀 Coding Education Agent")
    st.markdown("---")
    
    section = st.radio(
        "📑 Select Section",
        ["🏗️ Build", "🐛 Debug", "✅ Test", "⚡ Optimize", "📚 Explain", "🔍 Search", "💬 General"],
        key="section"
    )
    
    st.markdown("---")
    
    # Resources info
    with st.expander("💾 Resources & Files", expanded=False):
        if st.session_state.generated_files:
            st.write("### Generated Files:")
            for file_info in st.session_state.generated_files:
                with st.expander(f"📄 {file_info['name']}"):
                    st.code(file_info['code'], language="python")
                    st.download_button(
                        f"⬇️ Download {file_info['name']}",
                        file_info['code'],
                        file_name=f"{file_info['name']}.py"
                    )
        else:
            st.info("No files generated yet. Start building code!")
    
    # Chat history
    with st.expander("💬 Chat History", expanded=False):
        if st.session_state.chat_history:
            for role, message in st.session_state.chat_history:
                if role == "user":
                    st.write(f"👤 **You**: {message[:100]}...")
                else:
                    st.write(f"🤖 **Agent**: {message[:100]}...")
        else:
            st.info("Chat history is empty")
    
    st.markdown("---")
    
    if st.button("🗑️ Clear All", use_container_width=True):
        st.session_state.chat_history = []
        st.session_state.generated_files = []
        st.success("✅ Cleared!")
        st.rerun()

# ==================== MAIN CONTENT ====================
st.title("🚀 Intelligent Coding Education Agent")
st.markdown("Learn to code with AI-powered assistance • Generate • Debug • Test • Optimize • Learn")



