import os
import re
import streamlit as st
from pathlib import Path
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from datetime import datetime
import requests
from urllib.parse import urlencode


st.set_page_config(
    page_title="Sorus AI Pro",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== CSS WITH IMPROVED POPUP ====================
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

    @keyframes fadeInBackdrop {
        from { opacity: 0; }
        to { opacity: 1; }
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

    /* FIXED MODAL POPUP */
    .modal-backdrop {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.5);
        z-index: 998;
        animation: fadeInBackdrop 0.3s ease-out;
    }

    .modal-content {
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 90%;
        max-width: 600px;
        max-height: 85vh;
        background: white;
        border-radius: 16px;
        padding: 30px;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
        z-index: 999;
        overflow-y: auto;
        animation: slideInRight 0.4s ease-out;
    }

    .modal-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
    }

    .modal-header h2 {
        color: #667eea;
        margin: 0;
        font-size: 24px;
    }

    .close-btn {
        background: #e74c3c;
        color: white;
        border: none;
        border-radius: 50%;
        width: 32px;
        height: 32px;
        font-size: 20px;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: all 0.2s;
    }

    .close-btn:hover {
        background: #c0392b;
        transform: scale(1.1);
    }

    .form-group {
        margin-bottom: 16px;
    }

    .form-group label {
        display: block;
        font-weight: 600;
        color: #333;
        margin-bottom: 6px;
        font-size: 14px;
    }

    .form-group input,
    .form-group textarea {
        width: 100%;
        padding: 10px 12px;
        border: 1px solid #d1d5db;
        border-radius: 8px;
        font-size: 14px;
        font-family: inherit;
        box-sizing: border-box;
    }

    .form-group textarea {
        resize: vertical;
        min-height: 100px;
    }

    .form-group input:focus,
    .form-group textarea:focus {
        border-color: #667eea;
        outline: none;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }

    .submit-btn {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 12px 20px;
        font-weight: 600;
        cursor: pointer;
        width: 100%;
        transition: all 0.3s;
        font-size: 15px;
    }

    .submit-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(102, 126, 234, 0.3);
    }

    .web-search-badge {
        display: inline-block;
        background: linear-gradient(135deg, rgba(46, 204, 113, 0.2), rgba(52, 152, 219, 0.2));
        color: #27ae60;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 700;
        margin: 8px 0;
        border: 1px solid rgba(46, 204, 113, 0.3);
    }

    .tavily-sources {
        background: rgba(52, 152, 219, 0.05);
        border-left: 4px solid #3498db;
        padding: 12px;
        margin: 12px 0;
        border-radius: 6px;
        font-size: 13px;
    }

    .tavily-sources a {
        color: #3498db;
        text-decoration: none;
        font-weight: 500;
    }

    .tavily-sources a:hover {
        text-decoration: underline;
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

    .loading-spinner {
        display: inline-block;
        animation: spin 1s linear infinite;
    }

    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
</style>
""", unsafe_allow_html=True)

# ==================== SETUP ====================
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", os.getenv("GROQ_API_KEY"))
TAVILY_API_KEY = st.secrets.get("TAVILY_API_KEY", os.getenv("TAVILY_API_KEY"))

if not GROQ_API_KEY:
    st.error("❌ Please set GROQ_API_KEY in .streamlit/secrets.toml")
    st.stop()

if not TAVILY_API_KEY:
    st.warning("⚠️ TAVILY_API_KEY not set. Web search features will be limited.")

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.9,
    api_key=GROQ_API_KEY
)

Path("generated_code").mkdir(exist_ok=True)

# Initialize session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "generated_files" not in st.session_state:
    st.session_state.generated_files = []
if "current_response" not in st.session_state:
    st.session_state.current_response = None
if "show_modal" not in st.session_state:
    st.session_state.show_modal = False
if "modal_type" not in st.session_state:
    st.session_state.modal_type = None

# ==================== TAVILY WEB SEARCH INTEGRATION ====================

def tavily_search(query):
    """Search using Tavily API - optimized for AI applications"""
    if not TAVILY_API_KEY:
        return {"success": False, "error": "Tavily API key not configured"}
    
    try:
        url = "https://api.tavily.com/search"
        payload = {
            "api_key": TAVILY_API_KEY,
            "query": query,
            "include_answer": True,
            "max_results": 5,
            "include_images": False,
            "search_depth": "advanced"
        }
        
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Extract answer and sources
            answer = data.get("answer", "")
            results = data.get("results", [])
            
            sources_text = ""
            for i, result in enumerate(results[:3], 1):
                sources_text += f"\n{i}. {result.get('title', '')}\n   {result.get('url', '')}"
            
            return {
                "success": True,
                "answer": answer,
                "sources": sources_text,
                "results": results
            }
        else:
            return {"success": False, "error": f"API error: {response.status_code}"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

def stream_response_with_web(placeholder, template, variables, include_web_search=False, search_query=None):
    """Stream response with Tavily web search integration"""
    
    web_context = ""
    sources_display = ""
    
    if include_web_search and search_query and TAVILY_API_KEY:
        with st.spinner("🔍 Searching web with Tavily..."):
            search_result = tavily_search(search_query)
            if search_result.get("success"):
                web_answer = search_result.get("answer", "")
                sources = search_result.get("sources", "")
                
                web_context = f"\n\n[WEB SEARCH CONTEXT]\n{web_answer}\n\nSOURCES:{sources}"
                sources_display = sources
    
    # Enhanced template with web context
    enhanced_template = template
    if web_context:
        enhanced_template = template + web_context
    
    prompt = PromptTemplate(template=enhanced_template, input_variables=list(variables.keys()))
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
    
    # Display sources if available
    if sources_display:
        with st.expander("📚 Sources used"):
            st.markdown(sources_display)
    
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

def show_disclaimer():
    st.markdown("---")
    st.info("⚠️ **Note from Sorus**: I'm an AI and can make mistakes. Always test and verify code before using in production!")

# ==================== MODAL COMPONENT ====================

def show_resource_modal(code):
    """Show resource analysis modal"""
    col1, col2, col3 = st.columns([1, 10, 1])
    
    with col2:
        st.markdown("""
        <div class="modal-backdrop" id="modal-backdrop"></div>
        <div class="modal-content">
            <div class="modal-header">
                <h2>⚙️ Resource Analysis</h2>
                <button class="close-btn" onclick="document.getElementById('modal-backdrop').remove()">✕</button>
            </div>
        """, unsafe_allow_html=True)
        
        with st.form("resource_analysis_form"):
            st.markdown('<div class="form-group">', unsafe_allow_html=True)
            memory = st.text_input("Memory Limit (MB)", value="512")
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('<div class="form-group">', unsafe_allow_html=True)
            time_limit = st.text_input("Time Limit (seconds)", value="10")
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('<div class="form-group">', unsafe_allow_html=True)
            input_size = st.text_input("Input Data Size", value="10000 elements")
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('<div class="form-group">', unsafe_allow_html=True)
            py_version = st.text_input("Python Version", value="3.10+")
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('<div class="form-group">', unsafe_allow_html=True)
            st.write("Available Dependencies")
            dependencies = st.text_area("", value="Standard library only", height=80, label_visibility="collapsed")
            st.markdown('</div>', unsafe_allow_html=True)
            
            if st.form_submit_button("🔍 Deep Analysis", use_container_width=True):
                analysis_ph = st.empty()
                
                analysis = stream_response_with_web(
                    analysis_ph,
                    "Perform DEEP resource-based analysis:\n\n"
                    "CONSTRAINTS:\n"
                    "- Memory: {mem} MB\n"
                    "- Time: {time} seconds\n"
                    "- Input: {size}\n"
                    "- Python: {py}\n"
                    "- Dependencies: {deps}\n\n"
                    "CODE:\n{code}\n\n"
                    "COMPREHENSIVE ANALYSIS:\n"
                    "1. RUNTIME ERRORS: All possible errors for these constraints\n"
                    "2. PERFORMANCE: Bottlenecks and execution time estimate\n"
                    "3. MEMORY: Will it fit? Memory usage per operation\n"
                    "4. EDGE CASES: Inputs that will break this code\n"
                    "5. COMPATIBILITY: Python version issues\n"
                    "6. OPTIMIZATION: Specific fixes for these constraints\n"
                    "7. WARNINGS: Any dangerous patterns\n\n"
                    "Be thorough and provide line-number references.",
                    {
                        "mem": memory,
                        "time": time_limit,
                        "size": input_size,
                        "py": py_version,
                        "deps": dependencies,
                        "code": code
                    },
                    include_web_search=True,
                    search_query=f"Python performance optimization {py_version} memory constraints"
                )
                
                st.success("✅ Deep analysis complete!")
        
        st.markdown("</div>", unsafe_allow_html=True)

# ==================== SIDEBAR ====================
st.sidebar.title("⚡ Sorus AI Pro")
st.sidebar.markdown("*Advanced Code Generation & Analysis*")
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
        st.rerun()

with col2:
    if st.button("🗑️ Clear All", use_container_width=True):
        st.session_state.chat_history = []
        st.session_state.generated_files = []
        st.rerun()

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
st.sidebar.markdown("**Made with ⚡ for Excellence**")

# ==================== MAIN TITLE ====================
st.title("⚡ Sorus AI Pro")
st.markdown("✨ Production-grade code generation with web intelligence and deep resource analysis")
st.markdown("---")

# ==================== 1. BUILD SECTION (GEMINI AI STYLE) ====================
if section == "🏗️ Build":
    st.subheader("🏗️ Build - Professional Code Generation")
    st.markdown("Describe what you want to build. I'll break it down step-by-step, showing you the plan before coding.")

    requirement = st.text_area(
        "📝 What do you want to build?",
        placeholder="Example: Create an efficient Python function to find all prime numbers up to N with comprehensive error handling and type hints",
        height=120,
        key="build_input"
    )
    
    use_web_search = st.checkbox("🌐 Search web for latest best practices", value=True)

    if st.button("🚀 Analyze & Build", use_container_width=True, key="build_btn"):
        if requirement:
            with st.spinner("⏳ Deep analysis..."):
                
                # PHASE 1: REQUIREMENT ANALYSIS
                st.markdown('<div class="phase-header">📋 Phase 1: Understanding Your Requirement</div>', unsafe_allow_html=True)
                analysis_ph = st.empty()
                
                analysis = stream_response_with_web(
                    analysis_ph,
                    "Analyze this requirement deeply and provide:\n\n"
                    "REQUIREMENT:\n{req}\n\n"
                    "PROVIDE:\n"
                    "1. WHAT YOU'RE BUILDING\n"
                    "   - Core purpose\n"
                    "   - Primary functionality\n"
                    "   - Expected behavior\n\n"
                    "2. KEY FEATURES TO IMPLEMENT\n"
                    "   - List each feature\n"
                    "   - Explain why it's needed\n"
                    "   - Prioritize features\n\n"
                    "3. CONSTRAINTS & REQUIREMENTS\n"
                    "   - Performance requirements\n"
                    "   - Size/scale constraints\n"
                    "   - Compatibility needs\n"
                    "   - Error handling requirements\n\n"
                    "4. POTENTIAL CHALLENGES\n"
                    "   - What could go wrong\n"
                    "   - Edge cases to handle\n"
                    "   - Performance bottlenecks\n\n"
                    "Be clear and structured.",
                    {"req": requirement},
                    include_web_search=use_web_search,
                    search_query=f"{requirement} requirements analysis"
                )
                
                st.write("")

                # PHASE 2: RESOURCES & DEPENDENCIES
                st.markdown('<div class="phase-header">📚 Phase 2: Resources & Dependencies</div>', unsafe_allow_html=True)
                resources_ph = st.empty()
                
                resources = stream_response_with_web(
                    resources_ph,
                    "For building this:\n{req}\n\n"
                    "PROVIDE:\n"
                    "1. REQUIRED LIBRARIES\n"
                    "   - Library name\n"
                    "   - Version (latest)\n"
                    "   - Why it's needed\n"
                    "   - Installation command\n\n"
                    "2. EXTERNAL RESOURCES\n"
                    "   - APIs needed\n"
                    "   - Data sources\n"
                    "   - Documentation links\n\n"
                    "3. PYTHON VERSION\n"
                    "   - Minimum version\n"
                    "   - Recommended version\n"
                    "   - Special features needed\n\n"
                    "4. ENVIRONMENT SETUP\n"
                    "   - Virtual environment\n"
                    "   - Configuration files\n"
                    "   - Setup commands\n\n"
                    "Format as actionable steps.",
                    {"req": requirement},
                    include_web_search=use_web_search,
                    search_query=f"{requirement} libraries dependencies requirements"
                )
                
                st.write("")

                # PHASE 3: ARCHITECTURE & DESIGN
                st.markdown('<div class="phase-header">🏛️ Phase 3: Architecture & Design Plan</div>', unsafe_allow_html=True)
                arch_ph = st.empty()
                
                architecture = stream_response_with_web(
                    arch_ph,
                    "Design the architecture for:\n{req}\n\n"
                    "PROVIDE:\n"
                    "1. OVERALL STRUCTURE\n"
                    "   - Main components\n"
                    "   - How they interact\n"
                    "   - Data flow diagram (text)\n\n"
                    "2. CLASS/FUNCTION DESIGN\n"
                    "   - Main classes needed\n"
                    "   - Primary functions\n"
                    "   - Method signatures\n"
                    "   - What each does\n\n"
                    "3. DATA STRUCTURES\n"
                    "   - Key data structures\n"
                    "   - Why chosen\n"
                    "   - Format/schema\n\n"
                    "4. ERROR HANDLING STRATEGY\n"
                    "   - Exception types\n"
                    "   - Error messages\n"
                    "   - Recovery strategies\n\n"
                    "5. TESTING APPROACH\n"
                    "   - Unit tests needed\n"
                    "   - Test cases\n"
                    "   - Edge cases\n\n"
                    "Be detailed and architectural.",
                    {"req": requirement},
                    include_web_search=use_web_search,
                    search_query=f"{requirement} architecture design patterns best practices"
                )
                
                st.write("")

                # PHASE 4: STEP-BY-STEP TASKS
                st.markdown('<div class="phase-header">✅ Phase 4: Step-by-Step Implementation Tasks</div>', unsafe_allow_html=True)
                tasks_ph = st.empty()
                
                tasks = stream_response_with_web(
                    tasks_ph,
                    "Create detailed step-by-step tasks for:\n{req}\n\n"
                    "PROVIDE:\n"
                    "List implementation tasks in order:\n\n"
                    "STEP 1: [Task Name]\n"
                    "├─ What to implement\n"
                    "├─ Expected code size\n"
                    "├─ Dependencies needed\n"
                    "├─ How to test\n"
                    "└─ Success criteria\n\n"
                    "STEP 2: [Next Task]\n"
                    "[Continue for all steps...]\n\n"
                    "Each step should be:\n"
                    "- Clear and concrete\n"
                    "- Buildable independently\n"
                    "- Testable separately\n"
                    "- ~50-100 lines of code\n\n"
                    "Include 6-8 logical steps total.",
                    {"req": requirement},
                    include_web_search=use_web_search,
                    search_query=f"{requirement} implementation steps tutorial"
                )
                
                st.write("")

                # PHASE 5: PRODUCTION CODE
                st.markdown('<div class="phase-header">⚙️ Phase 5: Production Code Generation</div>', unsafe_allow_html=True)
                code_ph = st.empty()
                
                generated_code = stream_response_with_web(
                    code_ph,
                    "Generate COMPLETE PRODUCTION CODE for:\n{req}\n\n"
                    "REQUIREMENTS:\n"
                    "✓ Implement all features from analysis\n"
                    "✓ Follow architecture design\n"
                    "✓ Include all steps in logical order\n"
                    "✓ Full type hints on all functions\n"
                    "✓ Comprehensive Google-style docstrings\n"
                    "✓ Complete error handling\n"
                    "✓ Input validation\n"
                    "✓ Edge case handling\n"
                    "✓ Clear variable and function names\n"
                    "✓ Comments on complex logic\n"
                    "✓ Multiple working examples\n"
                    "✓ No TODOs, no placeholders\n"
                    "✓ Production-ready and tested\n\n"
                    "CODE STRUCTURE:\n"
                    "1. Imports (all needed libraries)\n"
                    "2. Constants and configuration\n"
                    "3. Utility functions\n"
                    "4. Main classes/functions\n"
                    "5. Complete examples\n"
                    "6. Usage instructions\n\n"
                    "Return ONLY the complete, working code.\n"
                    "No explanations, just code.",
                    {"req": requirement},
                    include_web_search=use_web_search,
                    search_query=f"{requirement} Python implementation"
                )

            st.write("")

            # PHASE 6: BEST PRACTICES & TIPS
            st.markdown('<div class="phase-header">💡 Phase 6: Best Practices & Optimization Tips</div>', unsafe_allow_html=True)
            tips_ph = st.empty()
            
            tips = stream_response_with_web(
                tips_ph,
                "For this code:\n{code}\n\n"
                "PROVIDE:\n"
                "1. PERFORMANCE TIPS\n"
                "   - Optimization opportunities\n"
                "   - Time/space complexity\n"
                "   - Bottlenecks\n\n"
                "2. SECURITY CONSIDERATIONS\n"
                "   - Input validation\n"
                "   - Potential vulnerabilities\n"
                "   - Safe practices\n\n"
                "3. TESTING RECOMMENDATIONS\n"
                "   - What to test\n"
                "   - Test cases\n"
                "   - How to verify\n\n"
                "4. MAINTENANCE TIPS\n"
                "   - Code clarity\n"
                "   - Documentation\n"
                "   - Common issues\n\n"
                "5. EXTENSION POINTS\n"
                "   - How to extend\n"
                "   - Future improvements\n"
                "   - Additional features\n\n"
                "Be practical and actionable.",
                {"code": generated_code},
                include_web_search=use_web_search,
                search_query=f"Python code best practices optimization"
            )
            
            # Store response
            st.session_state.current_response = {
                "code": generated_code,
                "req": requirement,
                "analysis": analysis,
                "resources": resources,
                "architecture": architecture,
                "tasks": tasks,
                "tips": tips,
                "type": "build"
            }
            
            add_to_history("user", requirement, "🏗️ Build")
            add_to_history("assistant", generated_code, "🏗️ Build")

            # Display final code
            st.markdown("---")
            if use_web_search:
                st.markdown('<div class="web-search-badge">🌐 Generated with web research</div>', unsafe_allow_html=True)
            
            st.markdown("### 🎯 Final Production Code")
            st.code(generated_code, language="python")

            # Action buttons
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("💾 Save Code", use_container_width=True):
                    filename = requirement[:25].replace(" ", "_")
                    path = save_code(filename, generated_code, "python")
                    st.success(f"✅ Saved!")
            
            with col2:
                if st.button("⚙️ Analyze Resources", use_container_width=True):
                    st.session_state.show_modal = True
                    st.session_state.modal_type = "resource"
            
            with col3:
                if st.button("📋 Copy Code", use_container_width=True):
                    st.info("✅ Ready to copy!")

            # Show modal if triggered
            if st.session_state.show_modal and st.session_state.modal_type == "resource":
                show_resource_modal(generated_code)
                st.session_state.show_modal = False

            # Follow-up questions
            st.markdown("---")
            st.markdown('<div class="followup-box">', unsafe_allow_html=True)
            st.markdown("### 🔄 Ask Follow-up Questions")
            
            followup = st.text_input(
                "Ask anything about the code, design, or implementation...",
                placeholder="e.g., How can I optimize this? Can I extend it to...?",
                key="build_followup"
            )
            
            if followup:
                followup_ph = st.empty()
                response = stream_response_with_web(
                    followup_ph,
                    "Answer this follow-up question:\n\n"
                    "Original requirement: {req}\n\n"
                    "Code:\n{code}\n\n"
                    "Question: {q}\n\n"
                    "Provide detailed, practical answer with code examples if needed.",
                    {"req": requirement, "code": generated_code, "q": followup},
                    include_web_search=use_web_search,
                    search_query=f"{followup} Python"
                )
                add_to_history("user", followup, "🏗️ Build")
                add_to_history("assistant", response, "🏗️ Build")
            
            st.markdown('</div>', unsafe_allow_html=True)
            show_disclaimer()
        else:
            st.warning("❌ Please describe what you want to build!")

# ==================== 2. DEBUG SECTION ====================
elif section == "🐛 Debug":
    st.subheader("🐛 Debug - Deep Issue Analysis")
    st.markdown("Paste broken code and I'll find and fix all issues")

    code_to_fix = st.text_area(
        "📝 Your broken code (with error if available):",
        placeholder="Paste your broken code here...",
        height=150,
        key="debug_code"
    )

    if st.button("🔧 Analyze & Fix", use_container_width=True, key="debug_btn"):
        if code_to_fix:
            with st.spinner("🔍 Deep analysis..."):
                
                # Analysis
                st.markdown('<div class="phase-header">🔍 Issue Analysis</div>', unsafe_allow_html=True)
                analysis_ph = st.empty()
                analysis = stream_response_with_web(
                    analysis_ph,
                    "DEEP analysis of broken code:\n1. All errors\n2. Root causes\n3. Why they occur\n4. Severity\n5. Related issues\n\nCode:\n{code}",
                    {"code": code_to_fix},
                    include_web_search=True,
                    search_query="Python debugging common errors"
                )

                st.write("")

                # Fix
                st.markdown('<div class="phase-header">✅ Fixed Code</div>', unsafe_allow_html=True)
                fix_ph = st.empty()
                fixed_code = stream_response_with_web(
                    fix_ph,
                    "Provide completely fixed, production-ready code:\n- Fix all errors\n- Add error handling\n- Add type hints\n- Add docstrings\n- Handle edge cases\n- Return ONLY code\n\nOriginal:\n{code}",
                    {"code": code_to_fix}
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
            followup = st.text_input("Ask about the fix...", key="debug_followup")
            if followup:
                followup_ph = st.empty()
                stream_response_with_web(followup_ph, "Code:\n{code}\n\nQ: {q}", {"code": fixed_code, "q": followup})
                add_to_history("user", followup, "🐛 Debug")
            st.markdown('</div>', unsafe_allow_html=True)
            show_disclaimer()
        else:
            st.warning("❌ Paste code to debug!")

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
            with st.spinner("🧪 Generating tests..."):
                
                st.markdown('<div class="phase-header">📋 Test Plan</div>', unsafe_allow_html=True)
                plan_ph = st.empty()
                test_plan = stream_response_with_web(
                    plan_ph,
                    "Plan comprehensive tests:\n{code}",
                    {"code": code},
                    include_web_search=True,
                    search_query="Python pytest best practices"
                )

                st.write("")

                st.markdown('<div class="phase-header">⚙️ Test Code</div>', unsafe_allow_html=True)
                test_ph = st.empty()
                test_code = stream_response_with_web(
                    test_ph,
                    "Generate production-ready tests:\n- Unit tests\n- Edge cases\n- Error scenarios\n- Integration tests\n\nCode:\n{code}",
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
                stream_response_with_web(followup_ph, "Tests:\n{code}\n\nQ: {q}", {"code": test_code, "q": followup})
            st.markdown('</div>', unsafe_allow_html=True)
            show_disclaimer()
        else:
            st.warning("❌ Paste code!")

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
            with st.spinner("🚀 Deep optimization..."):
                
                st.markdown('<div class="phase-header">📊 Performance Analysis</div>', unsafe_allow_html=True)
                analysis_ph = st.empty()
                analysis = stream_response_with_web(
                    analysis_ph,
                    "Detailed optimization analysis:\n{code}",
                    {"code": code},
                    include_web_search=True,
                    search_query="Python performance optimization algorithms"
                )

                st.write("")

                st.markdown('<div class="phase-header">⚙️ Optimized Code</div>', unsafe_allow_html=True)
                opt_ph = st.empty()
                optimized_code = stream_response_with_web(
                    opt_ph,
                    "Optimize for performance and memory:\n- Remove bottlenecks\n- Better algorithms\n- Memory efficiency\n- Pythonic patterns\n\nCode:\n{code}",
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
                stream_response_with_web(followup_ph, "Optimized:\n{code}\n\nQ: {q}", {"code": optimized_code, "q": followup})
            st.markdown('</div>', unsafe_allow_html=True)
            show_disclaimer()
        else:
            st.warning("❌ Paste code!")

# ==================== 5. EXPLAIN SECTION (IMPROVED) ====================
elif section == "📚 Explain":
    st.subheader("📚 Explain - Deep Learning Content")
    st.markdown("Learn concepts with detailed explanations and real-world examples")

    topic = st.text_area(
        "📝 What to explain?",
        placeholder="e.g., How does recursion work? Explain async/await in Python",
        height=120,
        key="explain_input"
    )
    
    use_web_search = st.checkbox("🌐 Include latest information and examples", value=True)

    if st.button("📖 Explain", use_container_width=True, key="explain_btn"):
        if topic:
            with st.spinner("📚 Creating detailed explanation..."):
                
                # SINGLE comprehensive explanation with web search
                st.markdown('<div class="phase-header">🎓 Comprehensive Explanation</div>', unsafe_allow_html=True)
                explain_ph = st.empty()
                explanation = stream_response_with_web(
                    explain_ph,
                    "Provide COMPREHENSIVE explanation:\n\n{topic}\n\n"
                    "Include:\n"
                    "1. Core concept explanation\n"
                    "2. Multiple detailed examples\n"
                    "3. Real-world use cases\n"
                    "4. Visual analogies\n"
                    "5. Common misconceptions\n"
                    "6. Step-by-step walkthrough\n"
                    "7. Pro tips and best practices\n"
                    "8. Performance considerations\n"
                    "9. Common pitfalls to avoid\n"
                    "10. Resources for deeper learning\n\n"
                    "Be thorough, clear, and engaging.",
                    {"topic": topic},
                    include_web_search=use_web_search,
                    search_query=f"{topic} tutorial best practices"
                )

            st.session_state.current_response = {
                "explanation": explanation,
                "topic": topic,
                "type": "explain"
            }
            add_to_history("user", f"Explain: {topic[:50]}...", "📚 Explain")
            add_to_history("assistant", explanation, "📚 Explain")

            st.markdown("---")
            if use_web_search:
                st.markdown('<div class="web-search-badge">🌐 Includes latest information</div>', unsafe_allow_html=True)

            st.markdown('<div class="followup-box">', unsafe_allow_html=True)
            st.markdown("### 🔄 Ask Follow-up Questions")
            followup = st.text_input(
                "Ask anything about this topic...",
                placeholder="e.g., Can you give another example? How is this related to...?",
                key="explain_followup"
            )
            if followup:
                followup_ph = st.empty()
                response = stream_response_with_web(
                    followup_ph,
                    "About: {topic}\n\nQuestion: {q}\n\nProvide detailed answer with examples.",
                    {"topic": topic, "q": followup},
                    include_web_search=use_web_search,
                    search_query=f"{topic} {followup}"
                )
                add_to_history("user", followup, "📚 Explain")
                add_to_history("assistant", response, "📚 Explain")
            st.markdown('</div>', unsafe_allow_html=True)
            show_disclaimer()
        else:
            st.warning("❌ Ask something to explain!")

# ==================== 6. SEARCH SECTION ====================
elif section == "🔍 Search":
    st.subheader("🔍 Search - Deep How-To Solutions")
    st.markdown("Find comprehensive solutions with code examples")

    problem = st.text_area(
        "❓ How to...",
        placeholder="e.g., How to handle large files efficiently? How to implement caching?",
        height=120,
        key="search_input"
    )

    if st.button("🔎 Find Solution", use_container_width=True, key="search_btn"):
        if problem:
            with st.spinner("🔍 Finding solution..."):
                
                st.markdown('<div class="phase-header">📋 Complete Solution</div>', unsafe_allow_html=True)
                solution_ph = st.empty()
                solution = stream_response_with_web(
                    solution_ph,
                    "Provide complete solution:\n\n{prob}\n\n"
                    "Include:\n"
                    "1. Problem explanation\n"
                    "2. Multiple solution approaches\n"
                    "3. Pros and cons of each\n"
                    "4. Complete code examples\n"
                    "5. Performance characteristics\n"
                    "6. When to use each approach\n"
                    "7. Common mistakes to avoid\n"
                    "8. Testing strategies\n\n"
                    "Be thorough and practical.",
                    {"prob": problem},
                    include_web_search=True,
                    search_query=f"{problem} Python implementation"
                )

            st.session_state.current_response = {"solution": solution, "problem": problem, "type": "search"}
            add_to_history("user", f"How to: {problem}", "🔍 Search")
            add_to_history("assistant", solution, "🔍 Search")

            st.markdown("---")
            st.markdown('<div class="web-search-badge">🌐 Web-enhanced solution</div>', unsafe_allow_html=True)

            st.markdown('<div class="followup-box">', unsafe_allow_html=True)
            followup = st.text_input("Follow-up question...", key="search_followup")
            if followup:
                followup_ph = st.empty()
                stream_response_with_web(followup_ph, "About: {prob}\n\nQ: {q}", {"prob": problem, "q": followup})
            st.markdown('</div>', unsafe_allow_html=True)
            show_disclaimer()
        else:
            st.warning("❌ Ask something!")

# ==================== 7. ASK SECTION ====================
else:
    st.subheader("💬 Ask Anything About Coding")
    st.markdown("Get comprehensive answers with examples and best practices")

    question = st.text_area(
        "❓ Your question:",
        placeholder="Ask anything about programming...",
        height=120,
        key="general_input"
    )

    if st.button("🤔 Ask", use_container_width=True, key="general_btn"):
        if question:
            with st.spinner("🤔 Thinking..."):
                
                st.markdown('<div class="phase-header">💡 Answer</div>', unsafe_allow_html=True)
                answer_ph = st.empty()
                answer = stream_response_with_web(
                    answer_ph,
                    "Answer comprehensively:\n\n{q}\n\n"
                    "Include:\n"
                    "1. Direct answer\n"
                    "2. Detailed explanation\n"
                    "3. Code examples\n"
                    "4. Use cases\n"
                    "5. Best practices\n"
                    "6. Common mistakes\n"
                    "7. Further resources\n\n"
                    "Be thorough and clear.",
                    {"q": question},
                    include_web_search=True,
                    search_query=question
                )

            st.session_state.current_response = {"answer": answer, "question": question, "type": "general"}
            add_to_history("user", question, "💬 Ask")
            add_to_history("assistant", answer, "💬 Ask")

            st.markdown("---")
            st.markdown('<div class="web-search-badge">🌐 Web-informed answer</div>', unsafe_allow_html=True)

            st.markdown('<div class="followup-box">', unsafe_allow_html=True)
            followup = st.text_input("Follow-up...", key="general_followup")
            if followup:
                followup_ph = st.empty()
                stream_response_with_web(followup_ph, "Q: {q}\n\nFollow-up: {follow}", {"q": question, "follow": followup})
            st.markdown('</div>', unsafe_allow_html=True)
            show_disclaimer()
        else:
            st.warning("❌ Ask something!")

# ==================== FOOTER ====================
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px 0;'>
    <p>⚡ Production-Grade Code Generation • AI-Powered Web Search • Deep Resource Analysis</p>
    <p style='font-size: 12px; margin-top: 10px;'>✨ Powered by Groq + LLaMA 3.3 70B + Tavily Search API</p>
    <p style='font-size: 11px; color: #999; margin-top: 6px;'>🔗 <a href='https://tavily.com' target='_blank'>Tavily API</a> • Real-time web intelligence for AI</p>
</div>
""", unsafe_allow_html=True)
