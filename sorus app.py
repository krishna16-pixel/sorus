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

    .phase-header {
        color: #667eea;
        font-size: 16px;
        font-weight: 700;
        margin: 16px 0 8px 0;
    }

    .code-block {
        background: #1e1e1e;
        border: 1px solid #333;
        border-radius: 8px;
        padding: 16px;
        margin: 12px 0;
        overflow-x: auto;
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
    temperature=0.85,
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
if "show_resource_modal" not in st.session_state:
    st.session_state.show_resource_modal = False
if "generated_code_for_resources" not in st.session_state:
    st.session_state.generated_code_for_resources = None

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

def stream_response(placeholder, template, variables):
    """Stream response from LLM with live updates"""
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

def add_to_history(role, content, section):
    """Add to chat history with metadata"""
    st.session_state.chat_history.append({
        "role": role,
        "content": content[:100] + "..." if len(content) > 100 else content,
        "full_content": content,
        "section": section,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
    })

def show_disclaimer():
    st.markdown("---")
    st.info("⚠️ **Note from Sorus**: I'm an AI and can make mistakes. Always test and verify code before using in production!")

def load_history_item(index):
    """Load a history item"""
    if 0 <= index < len(st.session_state.chat_history):
        item = st.session_state.chat_history[index]
        st.session_state.loaded_history = item
        st.rerun()

# ==================== SIDEBAR ====================
st.sidebar.title("🎓 Sorus AI")
st.sidebar.markdown("*Gemini-like Code Building*")
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
        
        st.sidebar.markdown(f"""
        <div class="history-item">
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
else:
    st.sidebar.markdown("*No files generated yet*")

st.sidebar.markdown("---")
st.sidebar.markdown("**Made with ❤️ for Learning**")

# ==================== MAIN TITLE ====================
st.title("🎓 Sorus AI")
st.markdown("✨ Build code like Gemini & Manus AI - Gather → Plan → Build → Analyze")
st.markdown("---")

# ==================== LOADED HISTORY DISPLAY ====================
if st.session_state.loaded_history:
    item = st.session_state.loaded_history
    st.info(f"📜 Loaded: {item['section']} • {item['timestamp']}")
    st.markdown(f"<div class='response-box'>{item['full_content']}</div>", unsafe_allow_html=True)
    st.markdown("---")

# ==================== 1. BUILD SECTION (GEMINI STYLE) ====================
if section == "🏗️ Build":
    st.subheader("🏗️ Build - Gemini Style Code Generation")
    st.markdown("Describe what you want to build. I'll gather info → plan → build like Gemini & Manus AI")

    requirement = st.text_area(
        "📝 What do you want to build?",
        placeholder="Example: Create a Python function to calculate fibonacci numbers with memoization",
        height=120,
        key="build_input"
    )

    if st.button("🚀 Start Building Process", use_container_width=True, key="build_btn"):
        if requirement:
            with st.spinner("⏳ Building your code..."):
                # PHASE 1: GATHER INFORMATION
                st.markdown('<div class="phase-header">📋 Phase 1: Gathering Information</div>', unsafe_allow_html=True)
                gather_ph = st.empty()
                gather_info = stream_response(
                    gather_ph,
                    "Analyze this requirement and identify:\n"
                    "1. What specifically needs to be built?\n"
                    "2. What technologies/libraries are needed?\n"
                    "3. Key constraints and dependencies?\n"
                    "4. What edge cases exist?\n\n"
                    "Requirement: {req}",
                    {"req": requirement}
                )

                st.write("")

                # PHASE 2: PLANNING
                st.markdown('<div class="phase-header">🎯 Phase 2: Planning Step-by-Step</div>', unsafe_allow_html=True)
                plan_ph = st.empty()
                planning = stream_response(
                    plan_ph,
                    "Create a detailed step-by-step plan for building:\n\n{req}\n\n"
                    "Include:\n"
                    "1. Architecture/structure\n"
                    "2. Key components\n"
                    "3. Implementation steps\n"
                    "4. Testing approach",
                    {"req": requirement}
                )

                st.write("")

                # PHASE 3: CODE GENERATION
                st.markdown('<div class="phase-header">⚙️ Phase 3: Generating Code</div>', unsafe_allow_html=True)
                code_ph = st.empty()
                generated_code = stream_response(
                    code_ph,
                    "Now generate the complete, production-ready code for:\n\n{req}\n\n"
                    "Return ONLY the code with inline comments explaining key parts.",
                    {"req": requirement}
                )

            # Store the generated code for the resource modal
            st.session_state.generated_code_for_resources = generated_code
            st.session_state.current_response = {
                "code": generated_code,
                "req": requirement,
                "gather": gather_info,
                "plan": planning,
                "type": "build"
            }
            
            add_to_history("user", requirement, "🏗️ Build")
            add_to_history("assistant", generated_code, "🏗️ Build")

            st.write("")
            st.markdown("---")

            # PHASE 4: SHOW CODE
            st.markdown('<div class="phase-header">✨ Final Code</div>', unsafe_allow_html=True)
            st.code(generated_code, language="python")

            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("💾 Save Code", use_container_width=True):
                    filename = requirement[:25].replace(" ", "_")
                    path = save_code(filename, generated_code, "python")
                    st.success(f"✅ Saved to: `{path}`")
            
            with col2:
                if st.button("⚠️ Check Resources & Errors", use_container_width=True):
                    st.session_state.show_resource_modal = True
            
            with col3:
                if st.button("📋 Copy Code", use_container_width=True):
                    st.info("Code ready to copy!")

            # PHASE 5: RESOURCE MODAL FOR ERROR DETECTION
            if st.session_state.show_resource_modal:
                st.markdown("---")
                st.markdown("### ⚙️ Specify Resources for Error Prediction")
                st.info("Tell me about your runtime environment so I can predict errors specific to your constraints")

                with st.form("resource_form"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        memory_limit = st.text_input(
                            "Memory Limit (MB)",
                            value="512",
                            help="Available RAM for execution"
                        )
                        time_limit = st.text_input(
                            "Time Limit (seconds)",
                            value="10",
                            help="Maximum execution time"
                        )
                        input_size = st.text_input(
                            "Input Data Size",
                            value="10000 elements",
                            help="Expected size of input data"
                        )
                    
                    with col2:
                        python_version = st.text_input(
                            "Python Version",
                            value="3.10+",
                            help="Target Python version"
                        )
                        dependencies = st.text_area(
                            "Available Dependencies",
                            value="Standard library only",
                            height=100,
                            help="Libraries/packages available"
                        )
                    
                    if st.form_submit_button("🔍 Predict Errors & Issues", use_container_width=True):
                        st.markdown('<div class="phase-header">🚨 Resource-Based Error & Issue Analysis</div>', unsafe_allow_html=True)
                        error_ph = st.empty()
                        
                        error_analysis = stream_response(
                            error_ph,
                            "Analyze this code and predict potential errors and issues given these resources:\n\n"
                            "Memory: {mem}\nTime: {time}\nInput Size: {size}\n"
                            "Python: {py_ver}\nDependencies: {deps}\n\n"
                            "Code:\n{code}\n\n"
                            "Provide:\n"
                            "1. Possible runtime errors\n"
                            "2. Performance bottlenecks\n"
                            "3. Memory overflow risks\n"
                            "4. Edge cases that fail\n"
                            "5. Solutions for each issue\n\n"
                            "Be specific and technical.",
                            {
                                "mem": memory_limit,
                                "time": time_limit,
                                "size": input_size,
                                "py_ver": python_version,
                                "deps": dependencies,
                                "code": st.session_state.generated_code_for_resources
                            }
                        )
                        
                        st.success("✅ Error analysis complete!")

            # Follow-up question
            st.markdown("---")
            st.markdown('<div class="followup-box">', unsafe_allow_html=True)
            st.markdown("### 🔄 Ask Follow-up Questions")
            followup = st.text_input(
                "Ask about the code or building process...",
                placeholder="e.g., How can I optimize this further?",
                key="build_followup"
            )
            
            if followup:
                followup_ph = st.empty()
                response = stream_response(
                    followup_ph,
                    "The user has a follow-up question:\n\nCode:\n{code}\n\nQuestion: {q}\n\n"
                    "Answer thoroughly with code examples.",
                    {"code": st.session_state.generated_code_for_resources, "q": followup}
                )
                add_to_history("user", followup, "🏗️ Build")
                add_to_history("assistant", response, "🏗️ Build")
            
            st.markdown('</div>', unsafe_allow_html=True)
            show_disclaimer()
        else:
            st.warning("Please tell me what you want to build!")

# ==================== 2. DEBUG SECTION ====================
elif section == "🐛 Debug":
    st.subheader("🐛 Debug - Fix Your Code")
    st.markdown("Paste your broken code and error message. I'll fix it with streaming analysis!")

    code_to_fix = st.text_area(
        "📝 Your broken code (with error in comments):",
        placeholder="Paste your broken code and error message here...",
        height=150,
        key="debug_code"
    )

    if st.button("🔧 Analyze & Fix", use_container_width=True, key="debug_btn"):
        if code_to_fix:
            with st.spinner("🔍 Analyzing code..."):
                # Analysis phase
                st.markdown('<div class="phase-header">🔍 Phase 1: Analysis</div>', unsafe_allow_html=True)
                analysis_ph = st.empty()
                analysis = stream_response(
                    analysis_ph,
                    "Analyze this broken code and identify:\n"
                    "1. What errors exist?\n"
                    "2. Why do they occur?\n"
                    "3. Impact on functionality\n\nCode:\n{code}",
                    {"code": code_to_fix}
                )

                st.write("")

                # Fix phase
                st.markdown('<div class="phase-header">✅ Phase 2: Fixed Code</div>', unsafe_allow_html=True)
                fix_ph = st.empty()
                fixed_code = stream_response(
                    fix_ph,
                    "Now provide the corrected code. Return ONLY the fixed code:\n\n{code}",
                    {"code": code_to_fix}
                )

                st.write("")

                # Explanation phase
                st.markdown('<div class="phase-header">📝 Phase 3: Explanation</div>', unsafe_allow_html=True)
                explain_ph = st.empty()
                explanation = stream_response(
                    explain_ph,
                    "Explain what was wrong and how it was fixed:\n\nOriginal:\n{orig}\n\nFixed:\n{fixed}",
                    {"orig": code_to_fix, "fixed": fixed_code}
                )

            st.session_state.current_response = {
                "fixed": fixed_code,
                "original": code_to_fix,
                "type": "debug"
            }
            add_to_history("user", f"Debug: {code_to_fix[:50]}...", "🐛 Debug")
            add_to_history("assistant", fixed_code, "🐛 Debug")

            st.markdown("---")
            st.code(fixed_code, language="python")

            if st.button("💾 Save Fixed Code", use_container_width=True):
                path = save_code("fixed_code", fixed_code, "python")
                st.success(f"✅ Saved!")

            # Follow-up
            st.markdown('<div class="followup-box">', unsafe_allow_html=True)
            followup = st.text_input("Follow-up question...", key="debug_followup")
            if followup:
                followup_ph = st.empty()
                response = stream_response(
                    followup_ph,
                    "Follow-up about the fix:\n{code}\n\nQuestion: {q}",
                    {"code": fixed_code, "q": followup}
                )
                add_to_history("user", followup, "🐛 Debug")
                add_to_history("assistant", response, "🐛 Debug")
            st.markdown('</div>', unsafe_allow_html=True)
            show_disclaimer()
        else:
            st.warning("Please paste your code!")

# ==================== 3. TEST SECTION ====================
elif section == "✅ Test":
    st.subheader("✅ Test - Generate Test Cases")
    st.markdown("Paste your code and I'll generate comprehensive test cases with streaming!")

    code = st.text_area(
        "📝 Your code:",
        placeholder="Paste your code here...",
        height=150,
        key="test_code"
    )

    if st.button("🧪 Generate Tests", use_container_width=True, key="test_btn"):
        if code:
            with st.spinner("🧪 Generating tests..."):
                st.markdown('<div class="phase-header">📋 Phase 1: Planning Tests</div>', unsafe_allow_html=True)
                plan_ph = st.empty()
                test_plan = stream_response(
                    plan_ph,
                    "Plan comprehensive test cases for this code:\n{code}",
                    {"code": code}
                )

                st.write("")

                st.markdown('<div class="phase-header">⚙️ Phase 2: Test Code</div>', unsafe_allow_html=True)
                test_ph = st.empty()
                test_code = stream_response(
                    test_ph,
                    "Generate test code. Return ONLY the test code:\n\n{code}",
                    {"code": code}
                )

            st.session_state.current_response = {"tests": test_code, "code": code, "type": "test"}
            add_to_history("user", f"Test: {code[:50]}...", "✅ Test")
            add_to_history("assistant", test_code, "✅ Test")

            st.markdown("---")
            st.code(test_code, language="python")

            if st.button("💾 Save Tests", use_container_width=True):
                save_code("test_cases", test_code, "python")
                st.success("✅ Saved!")

            st.markdown('<div class="followup-box">', unsafe_allow_html=True)
            followup = st.text_input("Follow-up...", key="test_followup")
            if followup:
                followup_ph = st.empty()
                stream_response(followup_ph, "Q about testing:\n{code}\n\nQ: {q}", {"code": code, "q": followup})
            st.markdown('</div>', unsafe_allow_html=True)
            show_disclaimer()
        else:
            st.warning("Paste code!")

# ==================== 4. OPTIMIZE SECTION ====================
elif section == "⚡ Optimize":
    st.subheader("⚡ Optimize - Improve Performance")

    code = st.text_area(
        "📝 Your code:",
        placeholder="Paste code...",
        height=150,
        key="opt_code"
    )

    if st.button("⚡ Optimize", use_container_width=True, key="opt_btn"):
        if code:
            with st.spinner("🚀 Optimizing..."):
                st.markdown('<div class="phase-header">📊 Phase 1: Analysis</div>', unsafe_allow_html=True)
                analysis_ph = st.empty()
                analysis = stream_response(
                    analysis_ph,
                    "Analyze this code for optimization opportunities:\n{code}",
                    {"code": code}
                )

                st.write("")

                st.markdown('<div class="phase-header">⚙️ Phase 2: Optimized Code</div>', unsafe_allow_html=True)
                opt_ph = st.empty()
                optimized_code = stream_response(
                    opt_ph,
                    "Return ONLY the optimized code:\n\n{code}",
                    {"code": code}
                )

            st.session_state.current_response = {"optimized": optimized_code, "original": code, "type": "optimize"}
            add_to_history("user", f"Optimize: {code[:50]}...", "⚡ Optimize")
            add_to_history("assistant", optimized_code, "⚡ Optimize")

            st.markdown("---")
            st.code(optimized_code, language="python")

            if st.button("💾 Save", use_container_width=True):
                save_code("optimized", optimized_code, "python")
                st.success("✅ Saved!")

            st.markdown('<div class="followup-box">', unsafe_allow_html=True)
            followup = st.text_input("Follow-up...", key="opt_followup")
            if followup:
                followup_ph = st.empty()
                stream_response(followup_ph, "Code optimization Q:\n{code}\n\nQ: {q}", {"code": optimized_code, "q": followup})
            st.markdown('</div>', unsafe_allow_html=True)
            show_disclaimer()
        else:
            st.warning("Paste code!")

# ==================== 5. EXPLAIN SECTION ====================
elif section == "📚 Explain":
    st.subheader("📚 Explain - Learn Concepts")

    topic = st.text_area(
        "📝 What to explain?",
        placeholder="e.g., What is recursion?",
        height=120,
        key="explain_input"
    )

    if st.button("📖 Explain", use_container_width=True, key="explain_btn"):
        if topic:
            with st.spinner("📚 Explaining..."):
                st.markdown('<div class="phase-header">🎓 Explanation</div>', unsafe_allow_html=True)
                explain_ph = st.empty()
                explanation = stream_response(
                    explain_ph,
                    "Explain in detail with examples:\n{topic}",
                    {"topic": topic}
                )

                st.write("")

                st.markdown('<div class="phase-header">⚠️ Common Mistakes</div>', unsafe_allow_html=True)
                mistakes_ph = st.empty()
                mistakes = stream_response(
                    mistakes_ph,
                    "5 mistakes beginners make with: {topic}",
                    {"topic": topic}
                )

                st.write("")

                st.markdown('<div class="phase-header">💡 Pro Tips</div>', unsafe_allow_html=True)
                tips_ph = st.empty()
                tips = stream_response(
                    tips_ph,
                    "5 pro tips for: {topic}",
                    {"topic": topic}
                )

            st.session_state.current_response = {"explanation": explanation, "mistakes": mistakes, "tips": tips, "topic": topic, "type": "explain"}
            add_to_history("user", f"Explain: {topic[:50]}...", "📚 Explain")
            add_to_history("assistant", explanation, "📚 Explain")

            st.markdown('<div class="followup-box">', unsafe_allow_html=True)
            followup = st.text_input("Follow-up...", key="explain_followup")
            if followup:
                followup_ph = st.empty()
                stream_response(followup_ph, "Follow-up on: {topic}\n\nQ: {q}", {"topic": topic, "q": followup})
            st.markdown('</div>', unsafe_allow_html=True)
            show_disclaimer()
        else:
            st.warning("Ask something!")

# ==================== 6. SEARCH SECTION ====================
elif section == "🔍 Search":
    st.subheader("🔍 Search - How-To Solutions")

    problem = st.text_area(
        "❓ How to...",
        placeholder="e.g., How to read files efficiently?",
        height=120,
        key="search_input"
    )

    if st.button("🔎 Search", use_container_width=True, key="search_btn"):
        if problem:
            with st.spinner("🔍 Finding solution..."):
                st.markdown('<div class="phase-header">📋 Solution</div>', unsafe_allow_html=True)
                solution_ph = st.empty()
                solution = stream_response(
                    solution_ph,
                    "How to: {prob}\n\nStep-by-step with code examples.",
                    {"prob": problem}
                )

            st.session_state.current_response = {"solution": solution, "problem": problem, "type": "search"}
            add_to_history("user", f"How to: {problem}", "🔍 Search")
            add_to_history("assistant", solution, "🔍 Search")

            st.markdown('<div class="followup-box">', unsafe_allow_html=True)
            followup = st.text_input("Follow-up...", key="search_followup")
            if followup:
                followup_ph = st.empty()
                stream_response(followup_ph, "Follow-up: {prob}\n\nQ: {q}", {"prob": problem, "q": followup})
            st.markdown('</div>', unsafe_allow_html=True)
            show_disclaimer()
        else:
            st.warning("Ask something!")

# ==================== 7. ASK SECTION ====================
else:
    st.subheader("💬 Ask Anything")

    question = st.text_area(
        "❓ Your question:",
        placeholder="Ask anything...",
        height=120,
        key="general_input"
    )

    if st.button("🤔 Ask", use_container_width=True, key="general_btn"):
        if question:
            with st.spinner("🤔 Thinking..."):
                answer_ph = st.empty()
                answer = stream_response(
                    answer_ph,
                    "Answer thoroughly:\n\n{q}",
                    {"q": question}
                )

            st.session_state.current_response = {"answer": answer, "question": question, "type": "general"}
            add_to_history("user", question, "💬 Ask")
            add_to_history("assistant", answer, "💬 Ask")

            st.markdown('<div class="followup-box">', unsafe_allow_html=True)
            followup = st.text_input("Follow-up...", key="general_followup")
            if followup:
                followup_ph = st.empty()
                stream_response(followup_ph, "Follow-up: {q}\n\nNew: {follow}", {"q": question, "follow": followup})
            st.markdown('</div>', unsafe_allow_html=True)
            show_disclaimer()
        else:
            st.warning("Ask something!")

# ==================== FOOTER ====================
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px 0;'>
    <p>🎓 Build Like Gemini & Manus AI • Gather → Plan → Build → Analyze</p>
    <p style='font-size: 12px; margin-top: 10px;'>✨ Powered by Groq + LLaMA 3.3 70B • Real-time Streaming</p>
</div>
""", unsafe_allow_html=True)
