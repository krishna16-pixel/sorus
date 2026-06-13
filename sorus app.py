import os
import streamlit as st
from pathlib import Path
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate

# ==================== PAGE CONFIG ====================
st.set_page_config(
    page_title="🚀 Coding Education Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== CSS ====================
st.markdown("""
<style>
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .stMarkdown { animation: fadeIn 0.3s ease-in; }
    
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 10px 20px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        width: 100% !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 10px 20px rgba(102, 126, 234, 0.4) !important;
    }
    
    .stTextArea textarea {
        border-radius: 8px !important;
        border: 2px solid #667eea !important;
    }
    
    .stTextInput input {
        border-radius: 8px !important;
        border: 2px solid #667eea !important;
    }
</style>
""", unsafe_allow_html=True)

# ==================== SETUP ====================
API_KEY = st.secrets.get("GOOGLE_API_KEY", os.getenv("GOOGLE_API_KEY"))

if not API_KEY:
    st.error("❌ Please set GOOGLE_API_KEY in .streamlit/secrets.toml")
    st.stop()

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.3, api_key=API_KEY)
Path("generated_code").mkdir(exist_ok=True)

# Initialize session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "generated_files" not in st.session_state:
    st.session_state.generated_files = []

# ==================== HELPER FUNCTIONS ====================

def save_code(filename, code, language):
    """Save generated code to file"""
    ext = {"python": "py", "javascript": "js", "java": "java", "cpp": "cpp"}.get(language, "txt")
    path = f"generated_code/{filename}.{ext}"
    with open(path, "w") as f:
        f.write(code)
    st.session_state.generated_files.append({"name": filename, "path": path, "code": code})
    return path

def run_chain(template, variables):
    """Run LLM chain without streaming"""
    prompt = PromptTemplate(template=template, input_variables=list(variables.keys()))
    chain = prompt | llm
    response = chain.invoke(variables)
    return response.content if hasattr(response, 'content') else str(response)

def stream_response(placeholder, template, variables):
    """Stream response character by character like ChatGPT"""
    prompt = PromptTemplate(template=template, input_variables=list(variables.keys()))
    chain = prompt | llm
    full_response = ""
    
    try:
        for chunk in chain.stream(variables):
            if hasattr(chunk, 'content'):
                full_response += chunk.content
            else:
                full_response += str(chunk)
            placeholder.markdown(full_response + "▌")
        
        placeholder.markdown(full_response)
    except Exception as e:
        # Fallback
        response = chain.invoke(variables)
        full_response = response.content if hasattr(response, 'content') else str(response)
        placeholder.markdown(full_response)
    
    return full_response

def show_disclaimer():
    """Show disclaimer after each response"""
    st.markdown("---")
    st.info("⚠️ **Note from Sorus**: I'm an AI and can make mistakes. Always test and verify code before using in production!")

# ==================== SIDEBAR ====================
st.sidebar.title("🚀 Sorus AI")
st.sidebar.markdown("Coding Education Agent")
st.sidebar.markdown("---")

section = st.sidebar.radio(
    "📑 Choose Section:",
    ["🏗️ Build", "🐛 Debug", "✅ Test", "⚡ Optimize", "📚 Explain", "🔍 Search", "💬 General"]
)

st.sidebar.markdown("---")

if st.sidebar.button("🗑️ Clear History", use_container_width=True):
    st.session_state.chat_history = []
    st.session_state.generated_files = []
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("""
**🎓 Educational Purpose Only**

Always verify generated code!
""")

# ==================== MAIN TITLE ====================
st.title("🚀 Intelligent Coding Education Agent")
st.markdown("**Sorus**: Your AI coding tutor • Learn • Build • Debug • Test")
st.markdown("---")

# ==================== 1. BUILD SECTION ====================
if section == "🏗️ Build":
    st.subheader("🏗️ Build - Generate Code")
    st.markdown("Tell me what you want to build, and I'll generate working code for you!")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        requirement = st.text_area(
            "📝 What do you want to build?",
            placeholder="Example: Create a Python function to calculate fibonacci numbers\nOr: Build a JavaScript function to sort an array",
            height=120,
            key="build_input"
        )
    
    with col2:
        language = st.selectbox(
            "Language",
            ["python", "javascript", "java", "cpp", "c"],
            key="build_lang"
        )
    
    memory = st.text_input("Memory limit (optional)", "512MB", key="build_mem")
    time_limit = st.text_input("Time limit (optional)", "30s", key="build_time")
    
    if st.button("🚀 Generate Code", use_container_width=True, key="build_btn"):
        if requirement:
            st.session_state.chat_history.append(("user", requirement))
            
            st.markdown("### Generated Code:")
            code_placeholder = st.empty()
            
            generated_code = stream_response(
                code_placeholder,
                "Create working {lang} code for: {req}\n\nReturn ONLY code without explanation.",
                {"lang": language, "req": requirement}
            )
            
            st.session_state.chat_history.append(("assistant", generated_code))
            
            # Save button
            if st.button("💾 Save This Code", key="save_build"):
                filename = requirement[:25].replace(" ", "_")
                path = save_code(filename, generated_code, language)
                st.success(f"✅ Code saved to: `{path}`")
            
            # Show error analysis
            st.markdown("---")
            st.markdown("### 📊 Possible Errors & Edge Cases:")
            error_placeholder = st.empty()
            
            stream_response(
                error_placeholder,
                "For this {lang} code with {mem} memory and {time} time limit:\n\n{code}\n\nList:\n1. Possible runtime errors\n2. Edge cases\n3. Common mistakes",
                {
                    "lang": language,
                    "code": generated_code,
                    "mem": memory,
                    "time": time_limit
                }
            )
            
            # Simple explanation
            st.markdown("---")
            st.markdown("### 💡 What This Code Does (Simple Explanation):")
            explain_placeholder = st.empty()
            
            stream_response(
                explain_placeholder,
                "Explain this {lang} code in very simple words, like explaining to a 5-year-old:\n\n{code}",
                {"lang": language, "code": generated_code}
            )
            
            show_disclaimer()
        else:
            st.warning("Please tell me what you want to build!")

# ==================== 2. DEBUG SECTION ====================
elif section == "🐛 Debug":
    st.subheader("🐛 Debug - Fix Your Code")
    st.markdown("Paste your broken code and the error message, and I'll fix it!")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        language = st.selectbox(
            "Language",
            ["python", "javascript", "java", "cpp", "c"],
            key="debug_lang"
        )
    
    with col2:
        pass
    
    code_to_fix = st.text_area(
        "📝 Your code:",
        placeholder="Paste your broken code here...",
        height=150,
        key="debug_code"
    )
    
    error_message = st.text_area(
        "❌ Error message:",
        placeholder="Paste the error message you're getting...",
        height=100,
        key="debug_error"
    )
    
    if st.button("🔧 Fix Code", use_container_width=True, key="debug_btn"):
        if code_to_fix and error_message:
            st.session_state.chat_history.append(("user", f"Debug: {code_to_fix[:50]}..."))
            
            st.markdown("### ✅ Fixed Code:")
            fixed_placeholder = st.empty()
            
            fixed_code = stream_response(
                fixed_placeholder,
                "Fix this {lang} code:\n\nBroken Code:\n{code}\n\nError:\n{err}\n\nReturn ONLY the corrected code.",
                {"lang": language, "code": code_to_fix, "err": error_message}
            )
            
            st.session_state.chat_history.append(("assistant", fixed_code))
            
            # Explanation
            st.markdown("---")
            st.markdown("### 📝 What Was Wrong?")
            explanation_placeholder = st.empty()
            
            stream_response(
                explanation_placeholder,
                "Explain what was wrong with this code and how the fix solves it:\n\nOriginal Error: {err}",
                {"err": error_message}
            )
            
            show_disclaimer()
        else:
            st.warning("Please paste both your code AND the error message!")

# ==================== 3. TEST SECTION ====================
elif section == "✅ Test":
    st.subheader("✅ Test - Generate Test Cases")
    st.markdown("Paste your code and I'll create test cases for it!")
    
    language = st.selectbox(
        "Language",
        ["python", "javascript", "java", "cpp", "c"],
        key="test_lang"
    )
    
    code = st.text_area(
        "📝 Your code:",
        placeholder="Paste your code here...",
        height=150,
        key="test_code"
    )
    
    if st.button("🧪 Generate Tests", use_container_width=True, key="test_btn"):
        if code:
            st.session_state.chat_history.append(("user", f"Test: {code[:50]}..."))
            
            st.markdown("### 🧪 Test Cases:")
            tests_placeholder = st.empty()
            
            test_code = stream_response(
                tests_placeholder,
                "Create comprehensive test cases for this {lang} code:\n\n{code}\n\nReturn ONLY test code.",
                {"lang": language, "code": code}
            )
            
            st.session_state.chat_history.append(("assistant", test_code))
            
            # Explanation
            st.markdown("---")
            st.markdown("### 📖 Test Explanation:")
            explanation_placeholder = st.empty()
            
            stream_response(
                explanation_placeholder,
                "Explain each test case and why it's important for testing this code properly.",
                {}
            )
            
            show_disclaimer()
        else:
            st.warning("Please paste your code!")

# ==================== 4. OPTIMIZE SECTION ====================
elif section == "⚡ Optimize":
    st.subheader("⚡ Optimize - Improve Your Code")
    st.markdown("Make your code faster, cleaner, and better!")
    
    language = st.selectbox(
        "Language",
        ["python", "javascript", "java", "cpp", "c"],
        key="opt_lang"
    )
    
    code = st.text_area(
        "📝 Your code:",
        placeholder="Paste your code here...",
        height=150,
        key="opt_code"
    )
    
    if st.button("⚡ Optimize", use_container_width=True, key="opt_btn"):
        if code:
            st.session_state.chat_history.append(("user", f"Optimize: {code[:50]}..."))
            
            st.markdown("### ⚡ Optimized Code:")
            optimized_placeholder = st.empty()
            
            optimized_code = stream_response(
                optimized_placeholder,
                "Optimize this {lang} code for performance and readability:\n\n{code}\n\nReturn ONLY optimized code.",
                {"lang": language, "code": code}
            )
            
            st.session_state.chat_history.append(("assistant", optimized_code))
            
            # Improvements
            st.markdown("---")
            st.markdown("### 📊 Improvements Made:")
            improvements_placeholder = st.empty()
            
            stream_response(
                improvements_placeholder,
                "List the key improvements and why they make the code better.",
                {}
            )
            
            show_disclaimer()
        else:
            st.warning("Please paste your code!")

# ==================== 5. EXPLAIN SECTION ====================
elif section == "📚 Explain":
    st.subheader("📚 Explain - Learn Programming Concepts")
    st.markdown("Ask me to explain any programming concept or code!")
    
    topic_or_code = st.text_area(
        "📝 What do you want to understand?",
        placeholder="Examples:\n- What is recursion?\n- Explain loops\n- How do functions work?\n- Explain this code: def add(a,b): return a+b",
        height=150,
        key="explain_input"
    )
    
    if st.button("📖 Explain", use_container_width=True, key="explain_btn"):
        if topic_or_code:
            st.session_state.chat_history.append(("user", f"Explain: {topic_or_code[:50]}..."))
            
            st.markdown("### 🎓 Explanation (For Beginners):")
            explanation_placeholder = st.empty()
            
            explanation = stream_response(
                explanation_placeholder,
                "Explain this in very simple words using real-world examples:\n\n{topic}",
                {"topic": topic_or_code}
            )
            
            st.session_state.chat_history.append(("assistant", explanation))
            
            # Common mistakes
            st.markdown("---")
            st.markdown("### ⚠️ Common Mistakes:")
            mistakes_placeholder = st.empty()
            
            stream_response(
                mistakes_placeholder,
                "List 3-5 common mistakes beginners make when learning about: {topic}",
                {"topic": topic_or_code}
            )
            
            # Pro tips
            st.markdown("---")
            st.markdown("### 💡 Pro Tips:")
            tips_placeholder = st.empty()
            
            stream_response(
                tips_placeholder,
                "Give 3 pro tips for mastering: {topic}",
                {"topic": topic_or_code}
            )
            
            show_disclaimer()
        else:
            st.warning("Tell me what you want to understand!")

# ==================== 6. SEARCH SECTION ====================
elif section == "🔍 Search":
    st.subheader("🔍 Search - How-To Solutions")
    st.markdown("Ask me how to do something in programming!")
    
    problem = st.text_area(
        "❓ How to...",
        placeholder="Examples:\n- How to read a file in Python?\n- How to create a function in JavaScript?\n- How to sort an array?\n- How to handle errors in Python?",
        height=120,
        key="search_input"
    )
    
    if st.button("🔎 Search", use_container_width=True, key="search_btn"):
        if problem:
            st.session_state.chat_history.append(("user", f"How to: {problem}"))
            
            st.markdown("### 📋 Step-by-Step Solution:")
            solution_placeholder = st.empty()
            
            solution = stream_response(
                solution_placeholder,
                "How to: {prob}\n\nGive clear step-by-step instructions with working code examples.",
                {"prob": problem}
            )
            
            st.session_state.chat_history.append(("assistant", solution))
            
            show_disclaimer()
        else:
            st.warning("Ask me how to do something!")

# ==================== 7. GENERAL SECTION ====================
else: # General
    st.subheader("💬 Ask Anything About Coding")
    st.markdown("Ask any programming question and I'll help!")
    
    question = st.text_area(
        "❓ Your question:",
        placeholder="Ask anything about programming...",
        height=120,
        key="general_input"
    )
    
    if st.button("🤔 Ask", use_container_width=True, key="general_btn"):
        if question:
            st.session_state.chat_history.append(("user", question))
            
            st.markdown("### 💡 Answer:")
            answer_placeholder = st.empty()
            
            answer = stream_response(
                answer_placeholder,
                "Answer this programming question clearly and helpfully:\n\n{q}",
                {"q": question}
            )
            
            st.session_state.chat_history.append(("assistant", answer))
            
            show_disclaimer()
        else:
            st.warning("Ask me a question!")

# ==================== FOOTER ====================
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px 0;'>
    <p>🎓 Educational Purpose Only • Sorus is an AI and makes mistakes • Always verify code • Have fun learning! 🚀</p>
</div>
""", unsafe_allow_html=True)

