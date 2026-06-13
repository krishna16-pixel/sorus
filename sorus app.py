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

    @keyframes slideInRight {
        from { transform: translateX(400px); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
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

    /* Floating Resource Modal */
    .resource-popup {
        position: fixed;
        top: 80px;
        right: 20px;
        width: 420px;
        max-height: 600px;
        background: white;
        border: 2px solid #667eea;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
        z-index: 999;
        overflow-y: auto;
        animation: slideInRight 0.4s ease-out;
    }

    .resource-popup::-webkit-scrollbar {
        width: 6px;
    }

    .resource-popup::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 3px;
    }

    .resource-popup::-webkit-scrollbar-thumb {
        background: #667eea;
        border-radius: 3px;
    }

    .resource-popup h3 {
        color: #667eea;
        margin-top: 0;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .close-popup {
        background: #e74c3c;
        color: white;
        border: none;
        border-radius: 50%;
        width: 24px;
        height: 24px;
        cursor: pointer;
        font-size: 16px;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 0;
    }

    .close-popup:hover {
        background: #c0392b;
    }

    .resource-form {
        display: flex;
        flex-direction: column;
        gap: 12px;
    }

    .resource-form input {
        padding: 10px;
        border: 1px solid #d1d5db;
        border-radius: 6px;
        font-size: 14px;
    }

    .resource-form textarea {
        padding: 10px;
        border: 1px solid #d1d5db;
        border-radius: 6px;
        font-size: 14px;
        resize: vertical;
        min-height: 80px;
    }

    .resource-submit {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 6px;
        padding: 10px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s;
    }

    .resource-submit:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(102, 126, 234, 0.4);
    }

    .error-analysis {
        background: rgba(231, 76, 60, 0.05);
        border-left: 4px solid #e74c3c;
        padding: 12px;
        border-radius: 6px;
        margin-top: 12px;
        max-height: 300px;
        overflow-y: auto;
    }

    .error-analysis::-webkit-scrollbar {
        width: 4px;
    }

    .error-analysis::-webkit-scrollbar-thumb {
        background: #e74c3c;
        border-radius: 2px;
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
    temperature=0.9,
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
if "show_resource_popup" not in st.session_state:
    st.session_state.show_resource_popup = False
if "resource_analysis" not in st.session_state:
    st.session_state.resource_analysis = None

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
        st.rerun()

# ==================== SIDEBAR ====================
st.sidebar.title("🎓 Sorus AI")
st.sidebar.markdown("*Professional Code Builder*")
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
        st.session_state.show_resource_popup = False
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
            <div class="history-timestamp">{item['timestamp']}</div>
        </div>
        """, unsafe_allow_html=True)
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
st.sidebar.markdown("**Made with ❤️ for Excellence**")

# ==================== MAIN TITLE ====================
st.title("🎓 Sorus AI")
st.markdown("✨ Professional-grade code generation with deep analysis and streaming responses")
st.markdown("---")

# ==================== RESOURCE POPUP DISPLAY ====================
if st.session_state.show_resource_popup:
    resource_col = st.sidebar
    with resource_col:
        st.markdown("### ⚙️ Analyze for Your Resources")
        
        with st.form("resource_form_sidebar"):
            memory_limit = st.text_input(
                "Memory Limit (MB)",
                value="512",
                key="res_memory"
            )
            time_limit = st.text_input(
                "Time Limit (seconds)",
                value="10",
                key="res_time"
            )
            input_size = st.text_input(
                "Input Data Size",
                value="10000 elements",
                key="res_input"
            )
            python_version = st.text_input(
                "Python Version",
                value="3.10+",
                key="res_python"
            )
            dependencies = st.text_area(
                "Available Dependencies",
                value="Standard library only",
                height=80,
                key="res_deps"
            )
            
            if st.form_submit_button("🔍 Analyze", use_container_width=True):
                if st.session_state.current_response and "code" in st.session_state.current_response:
                    with st.spinner("🔍 Deep Analysis..."):
                        analysis_ph = st.empty()
                        
                        analysis = stream_response(
                            analysis_ph,
                            "Perform DEEP resource-based analysis of this code:\n\n"
                            "CONSTRAINTS:\n"
                            "- Memory: {mem} MB\n"
                            "- Time: {time} seconds\n"
                            "- Input: {size}\n"
                            "- Python: {py}\n"
                            "- Dependencies: {deps}\n\n"
                            "CODE:\n{code}\n\n"
                            "ANALYZE THOROUGHLY:\n"
                            "1. RUNTIME ERRORS: List all possible runtime errors specific to these constraints\n"
                            "2. PERFORMANCE: How will this perform? Will it timeout?\n"
                            "3. MEMORY: Will it exceed the memory limit? Where?\n"
                            "4. EDGE CASES: What inputs will break this code?\n"
                            "5. WARNINGS: Any dangerous patterns?\n"
                            "6. SOLUTIONS: Specific fixes for each issue\n"
                            "7. OPTIMIZATION: How to optimize for these constraints\n\n"
                            "Be extremely detailed and technical.",
                            {
                                "mem": memory_limit,
                                "time": time_limit,
                                "size": input_size,
                                "py": python_version,
                                "deps": dependencies,
                                "code": st.session_state.current_response["code"]
                            }
                        )
                        
                        st.session_state.resource_analysis = analysis
                        st.success("✅ Analysis complete!")

# ==================== 1. BUILD SECTION ====================
if section == "🏗️ Build":
    st.subheader("🏗️ Build - Professional Code Generation")
    st.markdown("Describe your requirement and get production-ready, deeply analyzed code")

    requirement = st.text_area(
        "📝 What do you want to build?",
        placeholder="Example: Create a Python function to efficiently find all prime numbers up to N with comprehensive error handling and type hints",
        height=120,
        key="build_input"
    )

    if st.button("🚀 Build Code", use_container_width=True, key="build_btn"):
        if requirement:
            # SINGLE CODE GENERATION FLOW
            with st.spinner("⏳ Analyzing requirement & building code..."):
                
                # PHASE 1: ANALYSIS
                st.markdown('<div class="phase-header">📋 Phase 1: Requirement Analysis</div>', unsafe_allow_html=True)
                analysis_ph = st.empty()
                analysis = stream_response(
                    analysis_ph,
                    "Thoroughly analyze this requirement and identify:\n"
                    "1. Core functionality needed\n"
                    "2. Required technologies and libraries\n"
                    "3. Constraints and edge cases\n"
                    "4. Performance considerations\n"
                    "5. Error handling needs\n"
                    "6. Type hints needed\n\n"
                    "Requirement: {req}",
                    {"req": requirement}
                )
                
                st.write("")

                # PHASE 2: ARCHITECTURE
                st.markdown('<div class="phase-header">🏛️ Phase 2: Architecture & Design</div>', unsafe_allow_html=True)
                arch_ph = st.empty()
                architecture = stream_response(
                    arch_ph,
                    "Design detailed architecture for:\n{req}\n\n"
                    "Include:\n"
                    "1. Overall structure\n"
                    "2. Key components and classes\n"
                    "3. Function signatures\n"
                    "4. Data flow\n"
                    "5. Error handling strategy",
                    {"req": requirement}
                )

                st.write("")

                # PHASE 3: CODE GENERATION (ONCE ONLY)
                st.markdown('<div class="phase-header">⚙️ Phase 3: Production Code</div>', unsafe_allow_html=True)
                code_ph = st.empty()
                
                generated_code = stream_response(
                    code_ph,
                    "Generate PRODUCTION-READY code for:\n{req}\n\n"
                    "REQUIREMENTS:\n"
                    "- Complete, ready-to-use code\n"
                    "- Full type hints\n"
                    "- Comprehensive docstrings\n"
                    "- Error handling and validation\n"
                    "- Edge case handling\n"
                    "- Clear variable names\n"
                    "- Comments on complex logic\n"
                    "- Example usage\n"
                    "- No placeholders or TODOs\n\n"
                    "Return ONLY the complete, production-ready code.",
                    {"req": requirement}
                )

            # Store response ONCE
            st.session_state.current_response = {
                "code": generated_code,
                "req": requirement,
                "analysis": analysis,
                "architecture": architecture,
                "type": "build"
            }
            
            add_to_history("user", requirement, "🏗️ Build")
            add_to_history("assistant", generated_code, "🏗️ Build")

            # Show generated code
            st.markdown("---")
            st.markdown("### ✨ Generated Code")
            st.code(generated_code, language="python")

            # Buttons
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("💾 Save Code", use_container_width=True):
                    filename = requirement[:25].replace(" ", "_")
                    path = save_code(filename, generated_code, "python")
                    st.success(f"✅ Saved!")
            
            with col2:
                if st.button("⚠️ Check Resources", use_container_width=True):
                    st.session_state.show_resource_popup = True
                    st.rerun()
            
            with col3:
                if st.button("📋 Copy", use_container_width=True):
                    st.info("Ready to copy!")

            # Show resource popup if triggered
            if st.session_state.show_resource_popup:
                st.markdown("---")
                st.markdown("### ⚙️ Analyze for Your Environment")
                
                with st.form("resource_form_main"):
                    col1, col2 = st.columns(2)
                    with col1:
                        memory = st.text_input("Memory (MB)", value="512")
                        time_limit = st.text_input("Time Limit (sec)", value="10")
                    with col2:
                        input_size = st.text_input("Input Size", value="10000 elements")
                        py_ver = st.text_input("Python Version", value="3.10+")
                    
                    dependencies = st.text_area("Dependencies Available", value="Standard library only", height=60)
                    
                    if st.form_submit_button("🔍 Predict Errors", use_container_width=True):
                        error_ph = st.empty()
                        
                        error_analysis = stream_response(
                            error_ph,
                            "DEEP ERROR ANALYSIS for this code with these resources:\n\n"
                            "ENVIRONMENT:\n"
                            "Memory: {mem}MB | Time: {time}s | Input: {size}\n"
                            "Python: {py} | Dependencies: {deps}\n\n"
                            "CODE:\n{code}\n\n"
                            "ANALYZE DEEPLY:\n"
                            "1. RUNTIME ERRORS: All possible errors for these constraints\n"
                            "2. PERFORMANCE: Speed analysis, bottlenecks\n"
                            "3. MEMORY: Will it fit? Where are the leaks?\n"
                            "4. EDGE CASES: What inputs break it?\n"
                            "5. COMPATIBILITY: Python version issues?\n"
                            "6. DEPENDENCY ISSUES: What dependencies are missing?\n"
                            "7. SOLUTIONS: Specific fixes for each problem\n"
                            "8. RECOMMENDATIONS: Best practices for your environment\n\n"
                            "Be thorough and specific. Provide line numbers if applicable.",
                            {
                                "mem": memory,
                                "time": time_limit,
                                "size": input_size,
                                "py": py_ver,
                                "deps": dependencies,
                                "code": generated_code
                            }
                        )
                        
                        st.success("✅ Deep analysis complete!")

            # Follow-ups
            st.markdown("---")
            st.markdown('<div class="followup-box">', unsafe_allow_html=True)
            st.markdown("### 🔄 Ask Follow-up Questions")
            
            followup = st.text_input(
                "Ask anything about the code...",
                placeholder="e.g., How can I optimize this? What if I need to handle X?",
                key="build_followup"
            )
            
            if followup:
                followup_ph = st.empty()
                response = stream_response(
                    followup_ph,
                    "Answer this follow-up question about the code:\n\n"
                    "Code:\n{code}\n\n"
                    "Question: {q}\n\n"
                    "Provide detailed, practical answer with code examples if needed.",
                    {"code": generated_code, "q": followup}
                )
                add_to_history("user", followup, "🏗️ Build")
                add_to_history("assistant", response, "🏗️ Build")
            
            st.markdown('</div>', unsafe_allow_html=True)
            show_disclaimer()
        else:
            st.warning("Please describe what you want to build!")

# ==================== 2. DEBUG SECTION ====================
elif section == "🐛 Debug":
    st.subheader("🐛 Debug - Deep Code Analysis")
    st.markdown("Paste broken code and I'll analyze deeply to find and fix all issues")

    code_to_fix = st.text_area(
        "📝 Your broken code (with error message):",
        placeholder="Paste your code with error message in comments...",
        height=150,
        key="debug_code"
    )

    if st.button("🔧 Deep Analysis & Fix", use_container_width=True, key="debug_btn"):
        if code_to_fix:
            with st.spinner("🔍 Analyzing deeply..."):
                
                # Analysis
                st.markdown('<div class="phase-header">🔍 Phase 1: Deep Issue Analysis</div>', unsafe_allow_html=True)
                analysis_ph = st.empty()
                analysis = stream_response(
                    analysis_ph,
                    "Perform DEEP analysis of this broken code:\n"
                    "1. Identify ALL errors\n"
                    "2. Root causes\n"
                    "3. Why they occur\n"
                    "4. Impact severity\n"
                    "5. Related issues\n\n"
                    "Code:\n{code}",
                    {"code": code_to_fix}
                )

                st.write("")

                # Fix
                st.markdown('<div class="phase-header">✅ Phase 2: Fixed Code</div>', unsafe_allow_html=True)
                fix_ph = st.empty()
                fixed_code = stream_response(
                    fix_ph,
                    "Provide the completely fixed, production-ready code:\n"
                    "- Fix all errors\n"
                    "- Add error handling\n"
                    "- Add type hints\n"
                    "- Add docstrings\n"
                    "- Add edge case handling\n"
                    "- Return ONLY the code\n\n"
                    "Original:\n{code}",
                    {"code": code_to_fix}
                )

                st.write("")

                # Explanation
                st.markdown('<div class="phase-header">📝 Phase 3: Detailed Explanation</div>', unsafe_allow_html=True)
                explain_ph = st.empty()
                explanation = stream_response(
                    explain_ph,
                    "Explain in detail:\n"
                    "1. What errors were present\n"
                    "2. Why they were bugs\n"
                    "3. How each fix addresses it\n"
                    "4. Best practices shown\n"
                    "5. How to avoid similar issues\n\n"
                    "Original:\n{orig}\n\nFixed:\n{fixed}",
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

            if st.button("💾 Save", use_container_width=True):
                save_code("fixed_code", fixed_code, "python")
                st.success("✅ Saved!")

            st.markdown('<div class="followup-box">', unsafe_allow_html=True)
            followup = st.text_input("Ask follow-up...", key="debug_followup")
            if followup:
                followup_ph = st.empty()
                stream_response(followup_ph, "Code: {code}\n\nQ: {q}", {"code": fixed_code, "q": followup})
                add_to_history("user", followup, "🐛 Debug")
            st.markdown('</div>', unsafe_allow_html=True)
            show_disclaimer()
        else:
            st.warning("Paste code!")

# ==================== 3. TEST SECTION ====================
elif section == "✅ Test":
    st.subheader("✅ Test - Comprehensive Test Generation")
    st.markdown("Generate deep, comprehensive test cases covering all scenarios")

    code = st.text_area(
        "📝 Your code:",
        placeholder="Paste code...",
        height=150,
        key="test_code"
    )

    if st.button("🧪 Generate Tests", use_container_width=True, key="test_btn"):
        if code:
            with st.spinner("🧪 Generating comprehensive tests..."):
                
                st.markdown('<div class="phase-header">📋 Phase 1: Test Planning</div>', unsafe_allow_html=True)
                plan_ph = st.empty()
                test_plan = stream_response(
                    plan_ph,
                    "Plan comprehensive test cases:\n{code}",
                    {"code": code}
                )

                st.write("")

                st.markdown('<div class="phase-header">⚙️ Phase 2: Test Code</div>', unsafe_allow_html=True)
                test_ph = st.empty()
                test_code = stream_response(
                    test_ph,
                    "Generate production-ready tests:\n"
                    "- Unit tests\n"
                    "- Edge cases\n"
                    "- Error scenarios\n"
                    "- Performance tests\n"
                    "- Integration tests\n\n"
                    "Code:\n{code}",
                    {"code": code}
                )

            st.session_state.current_response = {"tests": test_code, "code": code, "type": "test"}
            add_to_history("user", f"Test: {code[:50]}...", "✅ Test")
            add_to_history("assistant", test_code, "✅ Test")

            st.markdown("---")
            st.code(test_code, language="python")

            if st.button("💾 Save", use_container_width=True):
                save_code("test_cases", test_code, "python")
                st.success("✅ Saved!")

            st.markdown('<div class="followup-box">', unsafe_allow_html=True)
            followup = st.text_input("Follow-up...", key="test_followup")
            if followup:
                followup_ph = st.empty()
                stream_response(followup_ph, "Tests:\n{code}\n\nQ: {q}", {"code": test_code, "q": followup})
            st.markdown('</div>', unsafe_allow_html=True)
            show_disclaimer()
        else:
            st.warning("Paste code!")

# ==================== 4. OPTIMIZE SECTION ====================
elif section == "⚡ Optimize":
    st.subheader("⚡ Optimize - Deep Performance Enhancement")

    code = st.text_area(
        "📝 Your code:",
        placeholder="Paste code...",
        height=150,
        key="opt_code"
    )

    if st.button("⚡ Optimize", use_container_width=True, key="opt_btn"):
        if code:
            with st.spinner("🚀 Deep optimization analysis..."):
                
                st.markdown('<div class="phase-header">📊 Phase 1: Performance Analysis</div>', unsafe_allow_html=True)
                analysis_ph = st.empty()
                analysis = stream_response(
                    analysis_ph,
                    "Detailed optimization analysis:\n{code}",
                    {"code": code}
                )

                st.write("")

                st.markdown('<div class="phase-header">⚙️ Phase 2: Optimized Code</div>', unsafe_allow_html=True)
                opt_ph = st.empty()
                optimized_code = stream_response(
                    opt_ph,
                    "Optimize for performance, memory, readability:\n"
                    "- Remove bottlenecks\n"
                    "- Improve algorithms\n"
                    "- Better memory usage\n"
                    "- Pythonic code\n\n"
                    "Code:\n{code}",
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
                stream_response(followup_ph, "Optimized:\n{code}\n\nQ: {q}", {"code": optimized_code, "q": followup})
            st.markdown('</div>', unsafe_allow_html=True)
            show_disclaimer()
        else:
            st.warning("Paste code!")

# ==================== 5. EXPLAIN SECTION ====================
elif section == "📚 Explain":
    st.subheader("📚 Explain - Deep Learning Content")

    topic = st.text_area(
        "📝 What to explain?",
        placeholder="e.g., How does recursion work?",
        height=120,
        key="explain_input"
    )

    if st.button("📖 Explain", use_container_width=True, key="explain_btn"):
        if topic:
            with st.spinner("📚 Creating detailed explanation..."):
                
                st.markdown('<div class="phase-header">🎓 Comprehensive Explanation</div>', unsafe_allow_html=True)
                explain_ph = st.empty()
                explanation = stream_response(
                    explain_ph,
                    "Explain thoroughly with multiple examples:\n{topic}",
                    {"topic": topic}
                )

                st.write("")

                st.markdown('<div class="phase-header">⚠️ Common Mistakes</div>', unsafe_allow_html=True)
                mistakes_ph = st.empty()
                mistakes = stream_response(
                    mistakes_ph,
                    "5 common mistakes about: {topic}",
                    {"topic": topic}
                )

                st.write("")

                st.markdown('<div class="phase-header">💡 Pro Tips & Best Practices</div>', unsafe_allow_html=True)
                tips_ph = st.empty()
                tips = stream_response(
                    tips_ph,
                    "5 advanced tips for: {topic}",
                    {"topic": topic}
                )

            st.session_state.current_response = {"explanation": explanation, "mistakes": mistakes, "tips": tips, "topic": topic, "type": "explain"}
            add_to_history("user", f"Explain: {topic[:50]}...", "📚 Explain")
            add_to_history("assistant", explanation, "📚 Explain")

            st.markdown('<div class="followup-box">', unsafe_allow_html=True)
            followup = st.text_input("Follow-up...", key="explain_followup")
            if followup:
                followup_ph = st.empty()
                stream_response(followup_ph, "About: {topic}\n\nQ: {q}", {"topic": topic, "q": followup})
            st.markdown('</div>', unsafe_allow_html=True)
            show_disclaimer()
        else:
            st.warning("Ask something!")

# ==================== 6. SEARCH SECTION ====================
elif section == "🔍 Search":
    st.subheader("🔍 Search - Deep How-To Solutions")

    problem = st.text_area(
        "❓ How to...",
        placeholder="e.g., How to handle large files efficiently?",
        height=120,
        key="search_input"
    )

    if st.button("🔎 Search", use_container_width=True, key="search_btn"):
        if problem:
            with st.spinner("🔍 Finding deep solution..."):
                
                st.markdown('<div class="phase-header">📋 Complete Solution</div>', unsafe_allow_html=True)
                solution_ph = st.empty()
                solution = stream_response(
                    solution_ph,
                    "Detailed solution with code examples:\n{prob}",
                    {"prob": problem}
                )

            st.session_state.current_response = {"solution": solution, "problem": problem, "type": "search"}
            add_to_history("user", f"How to: {problem}", "🔍 Search")
            add_to_history("assistant", solution, "🔍 Search")

            st.markdown('<div class="followup-box">', unsafe_allow_html=True)
            followup = st.text_input("Follow-up...", key="search_followup")
            if followup:
                followup_ph = st.empty()
                stream_response(followup_ph, "About: {prob}\n\nQ: {q}", {"prob": problem, "q": followup})
            st.markdown('</div>', unsafe_allow_html=True)
            show_disclaimer()
        else:
            st.warning("Ask something!")

# ==================== 7. ASK SECTION ====================
else:
    st.subheader("💬 Ask Anything About Coding")

    question = st.text_area(
        "❓ Your question:",
        placeholder="Ask anything about programming...",
        height=120,
        key="general_input"
    )

    if st.button("🤔 Ask", use_container_width=True, key="general_btn"):
        if question:
            with st.spinner("🤔 Thinking deeply..."):
                
                st.markdown('<div class="phase-header">💡 Answer</div>', unsafe_allow_html=True)
                answer_ph = st.empty()
                answer = stream_response(
                    answer_ph,
                    "Answer comprehensively with examples:\n{q}",
                    {"q": question}
                )

            st.session_state.current_response = {"answer": answer, "question": question, "type": "general"}
            add_to_history("user", question, "💬 Ask")
            add_to_history("assistant", answer, "💬 Ask")

            st.markdown('<div class="followup-box">', unsafe_allow_html=True)
            followup = st.text_input("Follow-up...", key="general_followup")
            if followup:
                followup_ph = st.empty()
                stream_response(followup_ph, "Q: {q}\n\nFollow-up: {follow}", {"q": question, "follow": followup})
            st.markdown('</div>', unsafe_allow_html=True)
            show_disclaimer()
        else:
            st.warning("Ask something!")

# ==================== FOOTER ====================
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px 0;'>
    <p>🎓 Professional Code Generation • Deep Analysis • Streaming Responses</p>
    <p style='font-size: 12px; margin-top: 10px;'>✨ Powered by Groq + LLaMA 3.3 70B</p>
</div>
""", unsafe_allow_html=True)
