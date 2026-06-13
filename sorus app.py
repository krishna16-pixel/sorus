import os
import re
import streamlit as st
from pathlib import Path
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from datetime import datetime


st.set_page_config(
    page_title="Sorus AI",
    page_icon="➰",
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
        border: 1px solid #d1d5db !important;
        border-radius: 12px !important;
        padding: 12px !important;
        font-size: 15px !important;
    }

    .stTextArea textarea:focus {
        border: 1px solid #9ca3af !important;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1) !important;
    }

    .stTextInput input {
        border: 1px solid #d1d5db !important;
        border-radius: 12px !important;
        padding: 10px 12px !important;
        font-size: 15px !important;
    }

    .stTextInput input:focus {
        border: 1px solid #9ca3af !important;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1) !important;
    }

    .error-badge {
        display: inline-block;
        background: #e74c3c;
        color: white;
        border-radius: 20px;
        padding: 4px 14px;
        font-size: 14px;
        font-weight: 700;
        margin: 8px 0;
        cursor: pointer;
        letter-spacing: 0.5px;
    }

    .history-item {
        padding: 10px;
        margin: 6px 0;
        border-left: 4px solid #667eea;
        background: rgba(102, 126, 234, 0.1);
        border-radius: 6px;
        font-size: 13px;
        cursor: pointer;
        transition: all 0.2s;
        font-weight: 500;
    }

    .history-item:hover {
        background: rgba(102, 126, 234, 0.25);
        transform: translateX(4px);
        box-shadow: 0 2px 8px rgba(102, 126, 234, 0.2);
    }

    .file-item {
        padding: 8px 12px;
        margin: 4px 0;
        border-left: 3px solid #27ae60;
        background: rgba(39, 174, 96, 0.1);
        border-radius: 4px;
        font-size: 12px;
        word-break: break-all;
    }

    .response-box {
        background: rgba(102, 126, 234, 0.05);
        border-left: 4px solid #667eea;
        padding: 16px;
        border-radius: 8px;
        margin: 12px 0;
    }

    .followup-box {
        background: rgba(39, 174, 96, 0.05);
        border: 2px solid rgba(39, 174, 96, 0.2);
        padding: 14px;
        border-radius: 8px;
        margin: 16px 0;
    }

    .history-timestamp {
        font-size: 11px;
        color: #999;
        margin-top: 4px;
    }
</style>
""", unsafe_allow_html=True)

# ==================== SETUP ====================
API_KEY = st.secrets.get("GROQ_API_KEY", os.getenv("GROQ_API_KEY"))

if not API_KEY:
    st.error("❌ Please set GROQ_API_KEY in .streamlit/secrets.toml")
    st.stop()

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.8,  # Increased for more creative, Gemini-like responses
    api_key=API_KEY
)

Path("generated_code").mkdir(exist_ok=True)

# Initialize session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "generated_files" not in st.session_state:
    st.session_state.generated_files = []
if "current_response" not in st.session_state:
    st.session_state.current_response = None
if "loaded_history" not in st.session_state:
    st.session_state.loaded_history = None

# ==================== HELPER FUNCTIONS ====================

def save_code(filename, code, language):
    ext = {"python": "py", "javascript": "js", "java": "java", "cpp": "cpp"}.get(language, "txt")
    path = f"generated_code/{filename}.{ext}"
    with open(path, "w") as f:
        f.write(code)
    st.session_state.generated_files.append({
        "name": filename, 
        "path": path, 
        "code": code,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
    })
    return path

def run_chain_streaming(template, variables, placeholder):
    """Stream response from LLM"""
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
        response = chain.invoke(variables)
        full_response = response.content if hasattr(response, 'content') else str(response)
        placeholder.markdown(full_response)
    
    return full_response

def run_chain(template, variables):
    """Non-streaming response from LLM"""
    prompt = PromptTemplate(template=template, input_variables=list(variables.keys()))
    chain = prompt | llm
    response = chain.invoke(variables)
    return response.content if hasattr(response, 'content') else str(response)

def count_errors_in_text(text):
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    count = 0
    for line in lines:
        if re.match(r'^(\d+[\.\)]|[-•*])\s+', line):
            count += 1
    return max(count, 1)

def show_errors_badge(lang, code, memory, time_limit):
    error_text = run_chain(
        "For this {lang} code with {mem} memory and {time} time limit:\n\n{code}\n\n"
        "List possible runtime errors, edge cases, and common mistakes as a numbered list. Be thorough and detailed.",
        {"lang": lang, "code": code, "mem": memory, "time": time_limit}
    )
    count = count_errors_in_text(error_text)
    st.markdown(
        f'<span class="error-badge">⚠️ {count} Possible Error{"s" if count != 1 else ""} / Edge Cases found</span>',
        unsafe_allow_html=True
    )
    with st.expander("👁️ Click to view errors & edge cases"):
        st.markdown(error_text)

def show_disclaimer():
    st.markdown("---")
    st.info("⚠️ **Note from Sorus**: I'm an AI and can make mistakes. Always test and verify code before using in production!")

def add_to_history(role, content, section, response_type="text"):
    """Add to chat history with metadata"""
    st.session_state.chat_history.append({
        "role": role,
        "content": content[:100] + "..." if len(content) > 100 else content,
        "full_content": content,
        "section": section,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "type": response_type
    })

def load_history_item(index):
    """Load a history item"""
    if 0 <= index < len(st.session_state.chat_history):
        item = st.session_state.chat_history[index]
        st.session_state.loaded_history = item
        st.rerun()

# ==================== SIDEBAR ====================
st.sidebar.title("🎓 Sorus AI")
st.sidebar.markdown("*AI-Powered Learning Platform*")
st.sidebar.markdown("---")

sections = [
    "🏗️ Build",
    "🐛 Debug",
    "✅ Test",
    "⚡ Optimize",
    "📚 Explain",
    "🔍 Search",
    "💬 Ask"
]

section = st.sidebar.selectbox(
    "📑 Choose Section:",
    sections,
    key="section_select"
)

st.sidebar.markdown("---")

col1, col2 = st.sidebar.columns(2)
with col1:
    if st.button("🔄 New Chat", use_container_width=True):
        st.session_state.chat_history = []
        st.session_state.generated_files = []
        st.session_state.current_response = None
        st.session_state.loaded_history = None
        st.rerun()

with col2:
    if st.button("🗑️ Clear All", use_container_width=True):
        st.session_state.chat_history = []
        st.session_state.generated_files = []
        st.rerun()

# Display Chat History
st.sidebar.markdown("---")
st.sidebar.subheader("💬 Chat History")

if st.session_state.chat_history:
    for i, item in enumerate(st.session_state.chat_history):
        emoji = "👤" if item["role"] == "user" else "🤖"
        
        history_button = st.sidebar.markdown(f"""
        <div class="history-item" onclick="window.location.reload()">
            {emoji} {item['content']}
            <div class="history-timestamp">{item['timestamp']} • {item['section']}</div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.sidebar.button(f"Load", key=f"load_{i}", help="Load this response"):
            load_history_item(i)
else:
    st.sidebar.markdown("*No chat history yet*")

# Display Generated Files
st.sidebar.markdown("---")
st.sidebar.subheader("💾 Generated Files")

if st.session_state.generated_files:
    for file in st.session_state.generated_files:
        st.sidebar.markdown(f"""
        <div class="file-item">
            📄 {file['name']}
            <div class="history-timestamp">{file.get('timestamp', 'N/A')}</div>
        </div>
        """, unsafe_allow_html=True)
        st.sidebar.caption(f"Path: `{file['path']}`")
else:
    st.sidebar.markdown("*No files generated yet*")

st.sidebar.markdown("---")
st.sidebar.markdown("**Made with ❤️ for Learning**\n\nAlways verify generated code!")

# ==================== MAIN TITLE ====================
st.title("🎓 Sorus AI")
st.markdown("✨ Your AI-powered coding mentor. Generate, debug, optimize, and learn with detailed, streaming responses!")
st.markdown("---")

# ==================== LOADED HISTORY DISPLAY ====================
if st.session_state.loaded_history:
    item = st.session_state.loaded_history
    st.info(f"📜 Loaded: {item['section']} • {item['timestamp']}")
    
    if item['role'] == 'user':
        st.markdown("### 👤 Your Question:")
    else:
        st.markdown("### 🤖 Sorus Response:")
    
    st.markdown(f"<div class='response-box'>{item['full_content']}</div>", unsafe_allow_html=True)
    st.markdown("---")

# ==================== 1. BUILD SECTION ====================
if section == "🏗️ Build":
    st.subheader("🏗️ Build - Generate Code")
    st.markdown("Tell me what you want to build, and I'll generate detailed, working code for you!")

    with st.form("build_form", clear_on_submit=True):
        requirement = st.text_area(
            "📝 What do you want to build?",
            placeholder="Example: Create a Python function to calculate fibonacci numbers with memoization",
            height=120,
            key="build_input"
        )
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write("")  # Spacer
        with col2:
            submit = st.form_submit_button("🚀 Generate Code", use_container_width=True)
        
        if submit and requirement:
            with st.spinner("✨ Generating code with detailed explanations..."):
                # Generate code
                code_placeholder = st.empty()
                generated_code = run_chain_streaming(
                    "Create comprehensive, well-commented working code for: {req}\n\n"
                    "Include detailed comments, error handling, and examples. Return ONLY code without preamble.",
                    {"req": requirement},
                    code_placeholder
                )
            
            st.session_state.current_response = {
                "code": generated_code,
                "req": requirement,
                "type": "build"
            }
            add_to_history("user", requirement, "🏗️ Build")
            add_to_history("assistant", generated_code, "🏗️ Build", "code")

    # Show current response
    if st.session_state.current_response and st.session_state.current_response.get("type") == "build":
        r = st.session_state.current_response
        
        st.markdown("### ✨ Generated Code:")
        st.code(r["code"], language="python")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Save This Code", key="save_build", use_container_width=True):
                filename = r["req"][:25].replace(" ", "_")
                path = save_code(filename, r["code"], "python")
                st.success(f"✅ Saved to: `{path}`")
        with col2:
            if st.button("📋 Copy Code", key="copy_build", use_container_width=True):
                st.info("Code copied to clipboard!")

        # Explanation with streaming
        st.markdown("### 💡 What This Code Does:")
        explain_ph = st.empty()
        run_chain_streaming(
            "Explain this code in detail, covering:\n"
            "1. Main purpose\n2. How it works step-by-step\n3. Key functions/algorithms\n4. Example usage\n\nCode:\n{code}",
            {"code": r["code"]},
            explain_ph
        )

        # Follow-up question box
        st.markdown('<div class="followup-box">', unsafe_allow_html=True)
        st.markdown("### 🔄 Follow-up Question:")
        followup = st.text_input(
            "Ask a follow-up question about this code...",
            placeholder="e.g., How can I optimize this further?",
            key="build_followup"
        )
        
        if followup:
            followup_ph = st.empty()
            response = run_chain_streaming(
                "The user asked a follow-up question about the code:\n\nCode:\n{code}\n\nQuestion: {q}\n\n"
                "Answer thoroughly with code examples if needed.",
                {"code": r["code"], "q": followup},
                followup_ph
            )
            add_to_history("user", followup, "🏗️ Build")
            add_to_history("assistant", response, "🏗️ Build")
        
        st.markdown('</div>', unsafe_allow_html=True)
        show_disclaimer()

# ==================== 2. DEBUG SECTION ====================
elif section == "🐛 Debug":
    st.subheader("🐛 Debug - Fix Your Code")
    st.markdown("Paste your broken code and error message, and I'll fix it with detailed explanations!")

    with st.form("debug_form", clear_on_submit=True):
        code_to_fix = st.text_area(
            "📝 Your code (with error message in comments):",
            placeholder="Paste your broken code and error message here...",
            height=150,
            key="debug_code"
        )
        
        submit = st.form_submit_button("🔧 Fix Code", use_container_width=True)
        
        if submit and code_to_fix:
            with st.spinner("🔍 Analyzing and fixing code..."):
                fix_placeholder = st.empty()
                fixed_code = run_chain_streaming(
                    "Fix this code and return ONLY the corrected code with detailed comments:\n\n{code}",
                    {"code": code_to_fix},
                    fix_placeholder
                )
            
            st.session_state.current_response = {
                "fixed": fixed_code,
                "original": code_to_fix,
                "type": "debug"
            }
            add_to_history("user", f"Debug: {code_to_fix[:50]}...", "🐛 Debug")
            add_to_history("assistant", fixed_code, "🐛 Debug", "code")

    if st.session_state.current_response and st.session_state.current_response.get("type") == "debug":
        r = st.session_state.current_response
        
        st.markdown("### ✅ Fixed Code:")
        st.code(r["fixed"], language="python")

        if st.button("💾 Save Fixed Code", key="save_debug", use_container_width=True):
            filename = "fixed_code"
            path = save_code(filename, r["fixed"], "python")
            st.success(f"✅ Saved to: `{path}`")

        st.markdown("### 📝 What Was Wrong & How It Was Fixed:")
        explain_ph = st.empty()
        run_chain_streaming(
            "Explain in detail:\n1. What errors were in the original code\n2. Why they cause problems\n3. How the fixes address each issue\n4. Best practices shown in the fixed version\n\nOriginal:\n{orig}\n\nFixed:\n{fixed}",
            {"orig": r["original"], "fixed": r["fixed"]},
            explain_ph
        )

        # Follow-up
        st.markdown('<div class="followup-box">', unsafe_allow_html=True)
        st.markdown("### 🔄 Follow-up Question:")
        followup = st.text_input(
            "Ask about the fix or code...",
            placeholder="e.g., What other errors should I watch for?",
            key="debug_followup"
        )
        
        if followup:
            followup_ph = st.empty()
            response = run_chain_streaming(
                "Follow-up about debugging:\n{code}\n\nQuestion: {q}",
                {"code": r["fixed"], "q": followup},
                followup_ph
            )
            add_to_history("user", followup, "🐛 Debug")
            add_to_history("assistant", response, "🐛 Debug")
        
        st.markdown('</div>', unsafe_allow_html=True)
        show_disclaimer()

# ==================== 3. TEST SECTION ====================
elif section == "✅ Test":
    st.subheader("✅ Test - Generate Comprehensive Test Cases")
    st.markdown("Paste your code and I'll create detailed test cases covering edge cases!")

    with st.form("test_form", clear_on_submit=True):
        code = st.text_area(
            "📝 Your code:",
            placeholder="Paste your code here...",
            height=150,
            key="test_code"
        )
        
        submit = st.form_submit_button("🧪 Generate Tests", use_container_width=True)
        
        if submit and code:
            with st.spinner("🧪 Generating comprehensive test cases..."):
                test_placeholder = st.empty()
                test_code = run_chain_streaming(
                    "Create comprehensive test cases for this code including:\n"
                    "1. Happy path tests\n2. Edge cases\n3. Error handling\n4. Boundary tests\n\n"
                    "Return ONLY test code:\n\n{code}",
                    {"code": code},
                    test_placeholder
                )
            
            st.session_state.current_response = {
                "tests": test_code,
                "code": code,
                "type": "test"
            }
            add_to_history("user", f"Test: {code[:50]}...", "✅ Test")
            add_to_history("assistant", test_code, "✅ Test", "code")

    if st.session_state.current_response and st.session_state.current_response.get("type") == "test":
        r = st.session_state.current_response
        
        st.markdown("### 🧪 Test Cases:")
        st.code(r["tests"], language="python")

        if st.button("💾 Save Tests", key="save_test", use_container_width=True):
            path = save_code("test_cases", r["tests"], "python")
            st.success(f"✅ Saved to: `{path}`")

        st.markdown("### 📖 Test Explanation:")
        explain_ph = st.empty()
        run_chain_streaming(
            "Explain each test case thoroughly:\n1. What it tests\n2. Why it's important\n3. What scenarios it covers\n\nCode:\n{code}\n\nTests:\n{tests}",
            {"code": r["code"], "tests": r["tests"]},
            explain_ph
        )

        # Follow-up
        st.markdown('<div class="followup-box">', unsafe_allow_html=True)
        st.markdown("### 🔄 Follow-up Question:")
        followup = st.text_input(
            "Ask about testing...",
            placeholder="e.g., What other test cases should I add?",
            key="test_followup"
        )
        
        if followup:
            followup_ph = st.empty()
            response = run_chain_streaming(
                "Follow-up about testing code:\n{code}\n\nQuestion: {q}",
                {"code": r["code"], "q": followup},
                followup_ph
            )
            add_to_history("user", followup, "✅ Test")
            add_to_history("assistant", response, "✅ Test")
        
        st.markdown('</div>', unsafe_allow_html=True)
        show_disclaimer()

# ==================== 4. OPTIMIZE SECTION ====================
elif section == "⚡ Optimize":
    st.subheader("⚡ Optimize - Improve Your Code")
    st.markdown("Paste your code and I'll optimize it for performance, readability, and best practices!")

    with st.form("opt_form", clear_on_submit=True):
        code = st.text_area(
            "📝 Your code:",
            placeholder="Paste your code here...",
            height=150,
            key="opt_code"
        )
        
        submit = st.form_submit_button("⚡ Optimize", use_container_width=True)
        
        if submit and code:
            with st.spinner("🚀 Optimizing code..."):
                opt_placeholder = st.empty()
                optimized_code = run_chain_streaming(
                    "Optimize this code for:\n"
                    "1. Performance and speed\n2. Memory efficiency\n3. Code readability\n4. Pythonic practices\n\n"
                    "Return ONLY optimized code with comments explaining changes:\n\n{code}",
                    {"code": code},
                    opt_placeholder
                )
            
            st.session_state.current_response = {
                "optimized": optimized_code,
                "original": code,
                "type": "optimize"
            }
            add_to_history("user", f"Optimize: {code[:50]}...", "⚡ Optimize")
            add_to_history("assistant", optimized_code, "⚡ Optimize", "code")

    if st.session_state.current_response and st.session_state.current_response.get("type") == "optimize":
        r = st.session_state.current_response
        
        st.markdown("### ⚡ Optimized Code:")
        st.code(r["optimized"], language="python")

        if st.button("💾 Save Optimized Code", key="save_opt", use_container_width=True):
            path = save_code("optimized_code", r["optimized"], "python")
            st.success(f"✅ Saved to: `{path}`")

        st.markdown("### 📊 Improvements Made:")
        improvements_ph = st.empty()
        run_chain_streaming(
            "List and explain in detail the key improvements:\n"
            "1. Performance gains and why\n2. Memory optimizations\n3. Code quality improvements\n4. Best practices applied\n\n"
            "Original:\n{original}\n\nOptimized:\n{optimized}",
            {"original": r["original"], "optimized": r["optimized"]},
            improvements_ph
        )

        # Follow-up
        st.markdown('<div class="followup-box">', unsafe_allow_html=True)
        st.markdown("### 🔄 Follow-up Question:")
        followup = st.text_input(
            "Ask about optimization...",
            placeholder="e.g., How much faster is this version?",
            key="opt_followup"
        )
        
        if followup:
            followup_ph = st.empty()
            response = run_chain_streaming(
                "Follow-up about code optimization:\n{code}\n\nQuestion: {q}",
                {"code": r["optimized"], "q": followup},
                followup_ph
            )
            add_to_history("user", followup, "⚡ Optimize")
            add_to_history("assistant", response, "⚡ Optimize")
        
        st.markdown('</div>', unsafe_allow_html=True)
        show_disclaimer()

# ==================== 5. EXPLAIN SECTION ====================
elif section == "📚 Explain":
    st.subheader("📚 Explain - Master Programming Concepts")
    st.markdown("Ask me to explain any programming concept, pattern, or code in detail!")

    with st.form("explain_form", clear_on_submit=True):
        topic_or_code = st.text_area(
            "📝 What do you want to understand?",
            placeholder="Examples:\n- What is recursion?\n- Explain decorators\n- How do async/await work?",
            height=150,
            key="explain_input"
        )
        
        submit = st.form_submit_button("📖 Explain", use_container_width=True)
        
        if submit and topic_or_code:
            with st.spinner("📚 Preparing detailed explanation..."):
                # Main explanation
                explain_ph = st.empty()
                explanation = run_chain_streaming(
                    "Explain this in very clear, detailed words using real-world examples and code snippets:\n\n{topic}",
                    {"topic": topic_or_code},
                    explain_ph
                )

                # Common mistakes
                st.write("")
                mistakes_ph = st.empty()
                mistakes = run_chain_streaming(
                    "List 5 detailed common mistakes beginners make when learning about: {topic}",
                    {"topic": topic_or_code},
                    mistakes_ph
                )

                # Pro tips
                st.write("")
                tips_ph = st.empty()
                tips = run_chain_streaming(
                    "Give 5 advanced pro tips for mastering: {topic}",
                    {"topic": topic_or_code},
                    tips_ph
                )
            
            st.session_state.current_response = {
                "explanation": explanation,
                "mistakes": mistakes,
                "tips": tips,
                "topic": topic_or_code,
                "type": "explain"
            }
            add_to_history("user", f"Explain: {topic_or_code[:50]}...", "📚 Explain")
            add_to_history("assistant", explanation, "📚 Explain")

    if st.session_state.current_response and st.session_state.current_response.get("type") == "explain":
        r = st.session_state.current_response
        
        st.markdown("### 🎓 Explanation:")
        st.markdown(f"<div class='response-box'>{r['explanation']}</div>", unsafe_allow_html=True)

        st.markdown("### ⚠️ Common Mistakes:")
        st.markdown(f"<div class='response-box'>{r['mistakes']}</div>", unsafe_allow_html=True)

        st.markdown("### 💡 Pro Tips:")
        st.markdown(f"<div class='response-box'>{r['tips']}</div>", unsafe_allow_html=True)

        # Follow-up
        st.markdown('<div class="followup-box">', unsafe_allow_html=True)
        st.markdown("### 🔄 Follow-up Question:")
        followup = st.text_input(
            "Ask to dive deeper...",
            placeholder="e.g., Can you show me a real-world example?",
            key="explain_followup"
        )
        
        if followup:
            followup_ph = st.empty()
            response = run_chain_streaming(
                "Follow-up question about: {topic}\n\nQuestion: {q}",
                {"topic": r["topic"], "q": followup},
                followup_ph
            )
            add_to_history("user", followup, "📚 Explain")
            add_to_history("assistant", response, "📚 Explain")
        
        st.markdown('</div>', unsafe_allow_html=True)
        show_disclaimer()

# ==================== 6. SEARCH SECTION ====================
elif section == "🔍 Search":
    st.subheader("🔍 Search - How-To Solutions")
    st.markdown("Ask how to solve a specific programming problem!")

    with st.form("search_form", clear_on_submit=True):
        problem = st.text_area(
            "❓ How to...",
            placeholder="Examples:\n- How to read a large file efficiently?\n- How to handle exceptions properly?\n- How to use decorators?",
            height=120,
            key="search_input"
        )
        
        submit = st.form_submit_button("🔎 Search", use_container_width=True)
        
        if submit and problem:
            with st.spinner("🔍 Finding solution..."):
                solution_ph = st.empty()
                solution = run_chain_streaming(
                    "How to: {prob}\n\nProvide comprehensive step-by-step instructions with:\n"
                    "1. Detailed explanation\n2. Multiple working code examples\n3. Common pitfalls\n4. Best practices",
                    {"prob": problem},
                    solution_ph
                )
            
            st.session_state.current_response = {
                "solution": solution,
                "problem": problem,
                "type": "search"
            }
            add_to_history("user", f"How to: {problem}", "🔍 Search")
            add_to_history("assistant", solution, "🔍 Search")

    if st.session_state.current_response and st.session_state.current_response.get("type") == "search":
        r = st.session_state.current_response
        
        st.markdown("### 📋 Step-by-Step Solution:")
        st.markdown(f"<div class='response-box'>{r['solution']}</div>", unsafe_allow_html=True)

        # Follow-up
        st.markdown('<div class="followup-box">', unsafe_allow_html=True)
        st.markdown("### 🔄 Follow-up Question:")
        followup = st.text_input(
            "Ask for clarification...",
            placeholder="e.g., Can you show another approach?",
            key="search_followup"
        )
        
        if followup:
            followup_ph = st.empty()
            response = run_chain_streaming(
                "The user has a follow-up about: {prob}\n\nQuestion: {q}",
                {"prob": r["problem"], "q": followup},
                followup_ph
            )
            add_to_history("user", followup, "🔍 Search")
            add_to_history("assistant", response, "🔍 Search")
        
        st.markdown('</div>', unsafe_allow_html=True)
        show_disclaimer()

# ==================== 7. ASK SECTION ====================
else:
    st.subheader("💬 Ask Anything About Coding")
    st.markdown("Ask any programming question and get detailed, comprehensive answers!")

    with st.form("general_form", clear_on_submit=True):
        question = st.text_area(
            "❓ Your question:",
            placeholder="Ask anything about programming, coding, or development...",
            height=120,
            key="general_input"
        )
        
        submit = st.form_submit_button("🤔 Ask", use_container_width=True)
        
        if submit and question:
            with st.spinner("🤔 Thinking..."):
                answer_ph = st.empty()
                answer = run_chain_streaming(
                    "Answer this programming question thoroughly with examples and detailed explanation:\n\n{q}",
                    {"q": question},
                    answer_ph
                )
            
            st.session_state.current_response = {
                "answer": answer,
                "question": question,
                "type": "general"
            }
            add_to_history("user", question, "💬 Ask")
            add_to_history("assistant", answer, "💬 Ask")

    if st.session_state.current_response and st.session_state.current_response.get("type") == "general":
        r = st.session_state.current_response
        
        st.markdown("### 💡 Answer:")
        st.markdown(f"<div class='response-box'>{r['answer']}</div>", unsafe_allow_html=True)

        # Follow-up
        st.markdown('<div class="followup-box">', unsafe_allow_html=True)
        st.markdown("### 🔄 Follow-up Question:")
        followup = st.text_input(
            "Ask a follow-up...",
            placeholder="Dive deeper into any aspect...",
            key="general_followup"
        )
        
        if followup:
            followup_ph = st.empty()
            response = run_chain_streaming(
                "Follow-up to the question: {q}\n\nNew question: {follow}",
                {"q": r["question"], "follow": followup},
                followup_ph
            )
            add_to_history("user", followup, "💬 Ask")
            add_to_history("assistant", response, "💬 Ask")
        
        st.markdown('</div>', unsafe_allow_html=True)
        show_disclaimer()

# ==================== FOOTER ====================
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px 0;'>
    <p>🎓 Educational Purpose Only • Sorus is an AI and makes mistakes • Always verify code • Have fun learning! 🚀</p>
    <p style='font-size: 12px; margin-top: 10px;'>✨ Powered by Groq + LLaMA 3.3 70B • Real-time Streaming Responses</p>
</div>
""", unsafe_allow_html=True)
