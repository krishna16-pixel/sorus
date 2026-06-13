import os
import re
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

    .warning-badge {
        display: inline-block;
        background: #f39c12;
        color: white;
        border-radius: 20px;
        padding: 4px 14px;
        font-size: 14px;
        font-weight: 700;
        margin: 8px 0;
        cursor: pointer;
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

# Per-section response state keys
for key in ["build_result", "debug_result", "test_result", "opt_result",
            "explain_result", "search_result", "general_result"]:
    if key not in st.session_state:
        st.session_state[key] = None

# ==================== HELPER FUNCTIONS ====================

def save_code(filename, code, language):
    ext = {"python": "py", "javascript": "js", "java": "java", "cpp": "cpp"}.get(language, "txt")
    path = f"generated_code/{filename}.{ext}"
    with open(path, "w") as f:
        f.write(code)
    st.session_state.generated_files.append({"name": filename, "path": path, "code": code})
    return path

def run_chain(template, variables):
    prompt = PromptTemplate(template=template, input_variables=list(variables.keys()))
    chain = prompt | llm
    response = chain.invoke(variables)
    return response.content if hasattr(response, 'content') else str(response)

def stream_response(placeholder, template, variables):
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
    except Exception:
        response = chain.invoke(variables)
        full_response = response.content if hasattr(response, 'content') else str(response)
        placeholder.markdown(full_response)
    return full_response

def count_errors_in_text(text):
    """Count numbered items or bullet points as errors/issues"""
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    count = 0
    for line in lines:
        if re.match(r'^(\d+[\.\)]|[-•*])\s+', line):
            count += 1
    return max(count, 1)

def show_errors_badge(lang, code, memory, time_limit):
    """Fetch errors and show as a badge with expander"""
    error_text = run_chain(
        "For this {lang} code with {mem} memory and {time} time limit:\n\n{code}\n\n"
        "List possible runtime errors, edge cases, and common mistakes as a numbered list. Be concise.",
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
    for key in ["build_result", "debug_result", "test_result", "opt_result",
                "explain_result", "search_result", "general_result"]:
        st.session_state[key] = None
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("**🎓 Educational Purpose Only**\n\nAlways verify generated code!")

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
            placeholder="Example: Create a Python function to calculate fibonacci numbers",
            height=120,
            key="build_input"
        )
    with col2:
        language = st.selectbox("Language", ["python", "javascript", "java", "cpp", "c"], key="build_lang")

    col3, col4 = st.columns(2)
    with col3:
        memory = st.text_input("Memory limit (optional)", "512MB", key="build_mem")
    with col4:
        time_limit = st.text_input("Time limit (optional)", "30s", key="build_time")

    if st.button("🚀 Generate Code", use_container_width=True, key="build_btn"):
        if requirement:
            st.session_state.chat_history.append(("user", requirement))
            with st.spinner("Generating..."):
                generated_code = run_chain(
                    "Create working {lang} code for: {req}\n\nReturn ONLY code without explanation.",
                    {"lang": language, "req": requirement}
                )
            st.session_state.build_result = {
                "code": generated_code, "lang": language,
                "mem": memory, "time": time_limit, "req": requirement
            }
            st.session_state.chat_history.append(("assistant", generated_code))
        else:
            st.warning("Please tell me what you want to build!")

    # Always show result if exists
    if st.session_state.build_result:
        r = st.session_state.build_result
        st.markdown("### Generated Code:")
        st.code(r["code"], language=r["lang"])

        if st.button("💾 Save This Code", key="save_build"):
            filename = r["req"][:25].replace(" ", "_")
            path = save_code(filename, r["code"], r["lang"])
            st.success(f"✅ Saved to: `{path}`")

        # Error badge
        show_errors_badge(r["lang"], r["code"], r["mem"], r["time"])

        # Simple explanation
        st.markdown("### 💡 What This Code Does:")
        explain_ph = st.empty()
        stream_response(
            explain_ph,
            "Explain this {lang} code in very simple words:\n\n{code}",
            {"lang": r["lang"], "code": r["code"]}
        )
        show_disclaimer()

# ==================== 2. DEBUG SECTION ====================
elif section == "🐛 Debug":
    st.subheader("🐛 Debug - Fix Your Code")
    st.markdown("Paste your broken code and the error message, and I'll fix it!")

    language = st.selectbox("Language", ["python", "javascript", "java", "cpp", "c"], key="debug_lang")

    code_to_fix = st.text_area(
        "📝 Your broken code:",
        placeholder="Paste your broken code here...",
        height=150,
        key="debug_code"
    )

    error_message = st.text_area(
        "❌ Error message:",
        placeholder="Paste the error message you're getting...",
        height=80,
        key="debug_error"
    )

    if st.button("🔧 Fix Code", use_container_width=True, key="debug_btn"):
        if code_to_fix and error_message:
            st.session_state.chat_history.append(("user", f"Debug: {code_to_fix[:50]}..."))
            with st.spinner("Fixing..."):
                fixed_code = run_chain(
                    "Fix this {lang} code:\n\nBroken Code:\n{code}\n\nError:\n{err}\n\nReturn ONLY the corrected code.",
                    {"lang": language, "code": code_to_fix, "err": error_message}
                )
            st.session_state.debug_result = {
                "fixed": fixed_code, "lang": language, "err": error_message
            }
            st.session_state.chat_history.append(("assistant", fixed_code))
        else:
            st.warning("Please paste both your code AND the error message!")

    if st.session_state.debug_result:
        r = st.session_state.debug_result
        st.markdown("### ✅ Fixed Code:")
        st.code(r["fixed"], language=r["lang"])

        st.markdown("### 📝 What Was Wrong?")
        explain_ph = st.empty()
        stream_response(
            explain_ph,
            "Explain clearly what was wrong and how the fix solves it. Error was: {err}",
            {"err": r["err"]}
        )
        show_disclaimer()

# ==================== 3. TEST SECTION ====================
elif section == "✅ Test":
    st.subheader("✅ Test - Generate Test Cases")
    st.markdown("Paste your code and I'll create test cases for it!")

    language = st.selectbox("Language", ["python", "javascript", "java", "cpp", "c"], key="test_lang")

    code = st.text_area(
        "📝 Your code:",
        placeholder="Paste your code here...",
        height=150,
        key="test_code"
    )

    if st.button("🧪 Generate Tests", use_container_width=True, key="test_btn"):
        if code:
            st.session_state.chat_history.append(("user", f"Test: {code[:50]}..."))
            with st.spinner("Generating tests..."):
                test_code = run_chain(
                    "Create comprehensive test cases for this {lang} code:\n\n{code}\n\nReturn ONLY test code.",
                    {"lang": language, "code": code}
                )
            st.session_state.test_result = {"tests": test_code, "lang": language, "code": code}
            st.session_state.chat_history.append(("assistant", test_code))
        else:
            st.warning("Please paste your code!")

    if st.session_state.test_result:
        r = st.session_state.test_result
        st.markdown("### 🧪 Test Cases:")
        st.code(r["tests"], language=r["lang"])

        st.markdown("### 📖 Test Explanation:")
        explain_ph = st.empty()
        stream_response(
            explain_ph,
            "Explain each test case and why it's important for this {lang} code:\n\n{code}",
            {"lang": r["lang"], "code": r["code"]}
        )
        show_disclaimer()

# ==================== 4. OPTIMIZE SECTION ====================
elif section == "⚡ Optimize":
    st.subheader("⚡ Optimize - Improve Your Code")
    st.markdown("Make your code faster, cleaner, and better!")

    language = st.selectbox("Language", ["python", "javascript", "java", "cpp", "c"], key="opt_lang")

    code = st.text_area(
        "📝 Your code:",
        placeholder="Paste your code here...",
        height=150,
        key="opt_code"
    )

    if st.button("⚡ Optimize", use_container_width=True, key="opt_btn"):
        if code:
            st.session_state.chat_history.append(("user", f"Optimize: {code[:50]}..."))
            with st.spinner("Optimizing..."):
                optimized_code = run_chain(
                    "Optimize this {lang} code for performance and readability:\n\n{code}\n\nReturn ONLY optimized code.",
                    {"lang": language, "code": code}
                )
            st.session_state.opt_result = {"optimized": optimized_code, "lang": language, "original": code}
            st.session_state.chat_history.append(("assistant", optimized_code))
        else:
            st.warning("Please paste your code!")

    if st.session_state.opt_result:
        r = st.session_state.opt_result
        st.markdown("### ⚡ Optimized Code:")
        st.code(r["optimized"], language=r["lang"])

        st.markdown("### 📊 Improvements Made:")
        improvements_ph = st.empty()
        stream_response(
            improvements_ph,
            "List the key improvements made to optimize this {lang} code and why each improvement helps:\n\nOriginal:\n{original}\n\nOptimized:\n{optimized}",
            {"lang": r["lang"], "original": r["original"], "optimized": r["optimized"]}
        )
        show_disclaimer()

# ==================== 5. EXPLAIN SECTION ====================
elif section == "📚 Explain":
    st.subheader("📚 Explain - Learn Programming Concepts")
    st.markdown("Ask me to explain any programming concept or code!")

    topic_or_code = st.text_area(
        "📝 What do you want to understand?",
        placeholder="Examples:\n- What is recursion?\n- Explain loops\n- How do functions work?",
        height=150,
        key="explain_input"
    )

    if st.button("📖 Explain", use_container_width=True, key="explain_btn"):
        if topic_or_code:
            st.session_state.chat_history.append(("user", f"Explain: {topic_or_code[:50]}..."))
            with st.spinner("Explaining..."):
                explanation = run_chain(
                    "Explain this in very simple words using real-world examples:\n\n{topic}",
                    {"topic": topic_or_code}
                )
                mistakes = run_chain(
                    "List 3-5 common mistakes beginners make when learning about: {topic}",
                    {"topic": topic_or_code}
                )
                tips = run_chain(
                    "Give 3 pro tips for mastering: {topic}",
                    {"topic": topic_or_code}
                )
            st.session_state.explain_result = {
                "explanation": explanation, "mistakes": mistakes, "tips": tips
            }
            st.session_state.chat_history.append(("assistant", explanation))
        else:
            st.warning("Tell me what you want to understand!")

    if st.session_state.explain_result:
        r = st.session_state.explain_result
        st.markdown("### 🎓 Explanation:")
        st.markdown(r["explanation"])

        st.markdown("### ⚠️ Common Mistakes:")
        st.markdown(r["mistakes"])

        st.markdown("### 💡 Pro Tips:")
        st.markdown(r["tips"])
        show_disclaimer()

# ==================== 6. SEARCH SECTION ====================
elif section == "🔍 Search":
    st.subheader("🔍 Search - How-To Solutions")
    st.markdown("Ask me how to do something in programming!")

    problem = st.text_area(
        "❓ How to...",
        placeholder="Examples:\n- How to read a file in Python?\n- How to sort an array?\n- How to handle errors?",
        height=120,
        key="search_input"
    )

    if st.button("🔎 Search", use_container_width=True, key="search_btn"):
        if problem:
            st.session_state.chat_history.append(("user", f"How to: {problem}"))
            with st.spinner("Searching..."):
                solution = run_chain(
                    "How to: {prob}\n\nGive clear step-by-step instructions with working code examples.",
                    {"prob": problem}
                )
            st.session_state.search_result = {"solution": solution}
            st.session_state.chat_history.append(("assistant", solution))
        else:
            st.warning("Ask me how to do something!")

    if st.session_state.search_result:
        r = st.session_state.search_result
        st.markdown("### 📋 Step-by-Step Solution:")
        st.markdown(r["solution"])
        show_disclaimer()

# ==================== 7. GENERAL SECTION ====================
else:
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
            with st.spinner("Thinking..."):
                answer = run_chain(
                    "Answer this programming question clearly and helpfully:\n\n{q}",
                    {"q": question}
                )
            st.session_state.general_result = {"answer": answer}
            st.session_state.chat_history.append(("assistant", answer))
        else:
            st.warning("Ask me a question!")

    if st.session_state.general_result:
        r = st.session_state.general_result
        st.markdown("### 💡 Answer:")
        st.markdown(r["answer"])
        show_disclaimer()

# ==================== FOOTER ====================
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px 0;'>
    <p>🎓 Educational Purpose Only • Sorus is an AI and makes mistakes • Always verify code • Have fun learning! 🚀</p>
</div>
""", unsafe_allow_html=True)
