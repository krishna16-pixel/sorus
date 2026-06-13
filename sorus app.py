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
    page_title="Sorus AI ",
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
                sources_text += f"\n{i}. {result.get('title', '')}\n {result.get('url', '')}"
           
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
   
    prompt = PromptTemplate(template=enhanced_template, input_variables=list(variables.keys()) if variables else [])
    chain = prompt | llm
    full_response = ""
   
    try:
        for chunk in chain.stream(variables if variables else {}):
            if hasattr(chunk, 'content'):
                full_response += chunk.content
            else:
                full_response += str(chunk)
            placeholder.markdown(full_response + "▌")
       
        placeholder.markdown(full_response)
    except Exception as e:
        response = chain.invoke(variables if variables else {})
        full_response = response.content if hasattr(response, 'content') else str(response)
        placeholder.markdown(full_response)
   
    # Display sources if available
    if sources_display:
        with st.expander("📚 Sources used"):
            st.markdown(sources_display)
   
    return full_response

def run_chain(template, variables):
    """Non-streaming response from LLM"""
    prompt = PromptTemplate.from_template(template)
    chain = prompt | llm
    response = chain.invoke(variables if variables else {})
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
    """Save generated code to file"""
    ext = {"python": "py", "javascript": "js", "java": "java", "cpp": "cpp"}.get(language.lower(), "txt")
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
    """Show disclaimer message"""
    st.markdown("---")
    st.info("⚠️ **Note from Sorus**: Sorus is an AI and can make mistakes. Double check the responses.")

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
st.sidebar.title("Sorus AI ")
st.sidebar.markdown("""This coding agent is an AI-powered tool that generates and assists with writing, modifying, and analyzing code. All outputs are automatically generated and may contain errors, security vulnerabilities, incomplete logic, or outdated practices, and should not be treated as verified or production-ready. Users are solely responsible for reviewing, testing, and validating all generated code before use, including checking for correctness, performance, security risks, dependency safety, and licensing compliance.
""")
st.sidebar.markdown("---")

sections = [
    " Build",
    " Debug",
    " Test",
    " Optimize",
    " Explain",
    " Search",
    " Ask"
]

section = st.sidebar.selectbox(
    " Choose Section:",
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
st.sidebar.markdown("This coding agent is an AI-powered assistant designed to help with writing, debugging, and improving code across different programming languages. It can generate code snippets, suggest fixes, and explain programming concepts to support faster and more efficient development.")

# ==================== MAIN TITLE ====================
st.title("⚡ Sorus AI ")
st.markdown("💡 Outputs are AI-generated and may contain errors or incomplete implementations. Human review, testing, and validation are required before use in production environments.")
st.markdown("---")

# ==================== BUILD SECTION (REFACTORED) ====================
if section == " Build":
    st.subheader(" Build - Professional Code Generation")
    st.markdown("Describe what you want to build. We'll analyze requirements, fetch best practices, and generate production-ready code.")

    requirement = st.text_area(
        "📝 What do you want to build?",
        placeholder="Example: Create an efficient Python function to find all prime numbers up to N with comprehensive error handling and type hints",
        height=120,
        key="build_input"
    )
    
    col1, col2, col3 = st.columns(3)
    with col1:
        programming_language = st.selectbox("🔧 Language", ["Python", "JavaScript", "Java", "C++"], key="build_lang")
    with col2:
        use_web_search = st.checkbox("🌐 Web Search", value=True, key="build_web")
    with col3:
        advanced_analysis = st.checkbox("📊 Deep Analysis", value=False, key="build_deep")
    
    if st.button("🚀 Generate Code", use_container_width=True, key="build_submit"):
        if not requirement.strip():
            st.error("Please enter a requirement")
            st.stop()
        
        # ==================== PHASE 1: FETCH INFORMATION ====================
        st.subheader("📚 Step 1: Information Fetched")
        info_placeholder = st.empty()
        
        fetch_info_prompt = f"""Analyze this requirement and provide ONLY the following structured information:

REQUIREMENT: {requirement}
LANGUAGE: {programming_language}

Provide in this exact format:
1. KEY REQUIREMENTS (bullet points - what must be done)
2. EDGE CASES (potential issues to handle)
3. BEST PRACTICES (2-3 relevant patterns for {programming_language})
4. COMPLEXITY ESTIMATE (Time/Space complexity if applicable)

Be concise. No fluff."""
        
        info_response = run_chain(fetch_info_prompt, {})
        info_placeholder.markdown(info_response)
        add_to_history("assistant", info_response, "Build - Information")
        
        # ==================== PHASE 2: TASKS ====================
        st.subheader("✅ Step 2: Tasks to Complete")
        tasks_placeholder = st.empty()
        
        tasks_prompt = f"""Based on this requirement, break down the implementation into clear tasks:

REQUIREMENT: {requirement}
LANGUAGE: {programming_language}

List 4-6 specific, actionable tasks in order. Format:
1. [Task name] - [brief description]
2. [Task name] - [brief description]
...

Be specific and implementation-focused."""
        
        tasks_response = run_chain(tasks_prompt, {})
        tasks_placeholder.markdown(tasks_response)
        add_to_history("assistant", tasks_response, "Build - Tasks")
        
        # ==================== PHASE 3: RESOURCES ====================
        st.subheader("⚙️ Step 3: Required Resources")
        resources_placeholder = st.empty()
        
        resources_prompt = f"""For this {programming_language} implementation, specify resources needed:

REQUIREMENT: {requirement}

Format exactly as:
**DEPENDENCIES:**
- [library/module name]: [brief reason]

**MEMORY/PERFORMANCE:**
- [requirement]: [estimate]

**SPECIAL CONSIDERATIONS:**
- [any special setup needed]

Keep it practical and minimal."""
        
        resources_response = run_chain(resources_prompt, {})
        resources_placeholder.markdown(resources_response)
        add_to_history("assistant", resources_response, "Build - Resources")
        
        # ==================== PHASE 4: WEB SEARCH ====================
        if use_web_search:
            st.subheader("🔍 Step 4: Web Search Results")
            search_placeholder = st.empty()
            
            search_query = f"{' '.join(requirement.split()[0:5])} {programming_language} best practices 2024"
            
            with st.spinner("Searching latest best practices..."):
                search_result = tavily_search(search_query)
                
                if search_result.get("success"):
                    answer = search_result.get("answer", "No results")
                    sources = search_result.get("sources", "")
                    
                    search_placeholder.markdown(f"""
**Search Query:** {search_query}

{answer}
                    """)
                    
                    if sources:
                        with st.expander("📚 Sources"):
                            st.markdown(sources)
                    
                    add_to_history("assistant", f"Web Search: {answer[:200]}", "Build - Web Search")
        
        # ==================== PHASE 5: SINGLE FINAL CODE ====================
        st.subheader("💾 Step 5: Final Production-Ready Code")
        code_placeholder = st.empty()
        
        code_prompt = f"""Generate ONE complete, production-ready {programming_language} solution.

REQUIREMENT: {requirement}

REQUIREMENTS FOR CODE:
- Include ALL necessary imports at the top
- Add comprehensive docstrings/comments
- Include full error handling
- Add type hints (if applicable to {programming_language})
- Add at least 2-3 usage examples at the bottom (as comments or separate functions)
- Make it production-ready with no TODOs or placeholders
- Clean, readable formatting
- Handle edge cases

Return ONLY the complete code. No explanations, no sections. Just the full working solution that could be saved to a file and run immediately."""
        
        full_code = stream_response_with_web(
            code_placeholder,
            code_prompt,
            {},
            include_web_search=False
        )
        
        add_to_history("assistant", full_code, "Build - Final Code")
        
        # ==================== SAVE & OPTIONS ====================
        st.divider()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            filename = st.text_input("📁 Save as:", value=f"solution", key="build_filename")
        
        with col2:
            if st.button("💾 Save Code", use_container_width=True, key="build_save"):
                path = save_code(filename, full_code, programming_language.lower())
                st.success(f"✅ Saved to `{path}`")
        
        with col3:
            if st.button("📋 Copy Code", use_container_width=True, key="build_copy"):
                st.code(full_code, language=programming_language.lower())
        
        # ==================== OPTIONAL DEEP ANALYSIS ====================
        if advanced_analysis:
            st.subheader("🔬 Optional: Deep Resource Analysis")
            
            if st.button("Run Deep Analysis", key="build_deep_run"):
                show_resource_modal(full_code)
        
        show_disclaimer()

# ==================== DEBUG SECTION ====================
elif section == " Debug":
    st.subheader(" Debug - Code Analysis & Fixing")
    st.markdown("Paste code with issues. We'll analyze, identify bugs, and provide fixes.")
    
    code_input = st.text_area(
        "📝 Paste your code:",
        placeholder="Paste the buggy code here...",
        height=200,
        key="debug_input"
    )
    
    language = st.selectbox("🔧 Language:", ["Python", "JavaScript", "Java", "C++"], key="debug_lang")
    
    col1, col2 = st.columns(2)
    with col1:
        error_message = st.text_input("Error message (optional):", key="debug_error")
    with col2:
        context = st.text_input("Context (what should it do?):", key="debug_context")
    
    if st.button("🔍 Analyze & Fix", use_container_width=True, key="debug_submit"):
        if not code_input.strip():
            st.error("Please paste code")
            st.stop()
        
        st.subheader("🐛 Issues Found")
        issues_ph = st.empty()
        
        issues_prompt = f"""Analyze this {language} code and identify ALL bugs and issues:

CODE:
```
{code_input}
```

ERROR (if any): {error_message}
CONTEXT: {context}

List each issue with:
1. Line number (if applicable)
2. Description
3. Severity (Critical/High/Medium/Low)
4. Root cause

Be thorough."""
        
        issues = run_chain(issues_prompt, {})
        issues_ph.markdown(issues)
        add_to_history("assistant", issues, "Debug - Issues")
        
        st.subheader("✅ Fixed Code")
        fixed_ph = st.empty()
        
        fixed_prompt = f"""Provide the COMPLETE fixed {language} code. Address all issues found.

ORIGINAL CODE:
```
{code_input}
```

ERRORS: {error_message}

Return ONLY the complete fixed code, no explanations."""
        
        fixed_code = stream_response_with_web(fixed_ph, fixed_prompt, {}, include_web_search=False)
        add_to_history("assistant", fixed_code, "Debug - Fixed Code")
        
        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Save Fixed Code", use_container_width=True):
                name = st.text_input("Filename:", value="fixed_code", key="debug_save")
                if name:
                    path = save_code(name, fixed_code, language.lower())
                    st.success(f"✅ Saved to {path}")
        
        with col2:
            if st.button("📋 Copy Fixed Code", use_container_width=True):
                st.code(fixed_code, language=language.lower())
        
        show_disclaimer()

# ==================== TEST SECTION ====================
elif section == " Test":
    st.subheader(" Test - Generate Test Cases")
    st.markdown("Paste code and get comprehensive test cases.")
    
    code_input = st.text_area(
        "📝 Paste your code:",
        placeholder="Paste code to test...",
        height=200,
        key="test_input"
    )
    
    language = st.selectbox("🔧 Language:", ["Python", "JavaScript", "Java", "C++"], key="test_lang")
    
    col1, col2 = st.columns(2)
    with col1:
        test_framework = st.text_input("Test framework (pytest, jest, etc.):", value="pytest", key="test_framework")
    with col2:
        coverage = st.slider("Target Coverage %:", 50, 100, 80, key="test_coverage")
    
    if st.button("🧪 Generate Tests", use_container_width=True, key="test_submit"):
        if not code_input.strip():
            st.error("Please paste code")
            st.stop()
        
        st.subheader("📋 Test Cases Generated")
        tests_ph = st.empty()
        
        tests_prompt = f"""Generate comprehensive {test_framework} test cases for this {language} code.

CODE:
```
{code_input}
```

Requirements:
- Aim for {coverage}% code coverage
- Include unit tests
- Include edge case tests
- Include error handling tests
- Include integration tests if applicable
- Use {test_framework} framework/conventions
- Include setup/teardown if needed
- Provide complete, runnable test file

Return ONLY complete test code, ready to run."""
        
        tests_code = stream_response_with_web(tests_ph, tests_prompt, {}, include_web_search=False)
        add_to_history("assistant", tests_code, "Test - Generated Tests")
        
        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Save Tests", use_container_width=True):
                name = st.text_input("Filename:", value="test_suite", key="test_save")
                if name:
                    save_code(name, tests_code, language.lower())
                    st.success(f"✅ Tests saved")
        
        with col2:
            if st.button("📋 Copy Tests", use_container_width=True):
                st.code(tests_code, language=language.lower())
        
        show_disclaimer()

# ==================== OPTIMIZE SECTION ====================
elif section == " Optimize":
    st.subheader(" Optimize - Performance Improvement")
    st.markdown("Get optimization suggestions and improved code.")
    
    code_input = st.text_area(
        "📝 Paste your code:",
        placeholder="Paste code to optimize...",
        height=200,
        key="opt_input"
    )
    
    language = st.selectbox("🔧 Language:", ["Python", "JavaScript", "Java", "C++"], key="opt_lang")
    
    col1, col2 = st.columns(2)
    with col1:
        constraint = st.selectbox(
            "Optimize for:",
            ["Speed", "Memory", "Readability", "Balanced"],
            key="opt_constraint"
        )
    with col2:
        current_perf = st.text_input("Current performance (optional):", key="opt_perf")
    
    if st.button("⚡ Optimize Code", use_container_width=True, key="opt_submit"):
        if not code_input.strip():
            st.error("Please paste code")
            st.stop()
        
        st.subheader("📊 Optimization Analysis")
        analysis_ph = st.empty()
        
        analysis_prompt = f"""Analyze this {language} code for {constraint.lower()} optimization:

CODE:
```
{code_input}
```

Current Performance: {current_perf}

Provide:
1. Bottleneck Analysis
2. Specific Issues
3. Improvement Opportunities
4. Expected Impact

Be technical and specific."""
        
        analysis = run_chain(analysis_prompt, {})
        analysis_ph.markdown(analysis)
        add_to_history("assistant", analysis, "Optimize - Analysis")
        
        st.subheader(" Optimized Code")
        optimized_ph = st.empty()
        
        optimized_prompt = f"""Provide completely optimized {language} code for {constraint.lower()}:

ORIGINAL:
```
{code_input}
```

Optimize for: {constraint}

Return ONLY the complete optimized code with improvements applied."""
        
        optimized_code = stream_response_with_web(optimized_ph, optimized_prompt, {}, include_web_search=False)
        add_to_history("assistant", optimized_code, "Optimize - Code")
        
        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Save Optimized", use_container_width=True):
                name = st.text_input("Filename:", value="optimized_code", key="opt_save")
                if name:
                    save_code(name, optimized_code, language.lower())
                    st.success(f"✅ Saved")
        
        with col2:
            if st.button("📋 Copy", use_container_width=True):
                st.code(optimized_code, language=language.lower())
        
        show_disclaimer()

# ==================== EXPLAIN SECTION ====================
elif section == " Explain":
    st.subheader(" Explain - Code Understanding")
    st.markdown("Paste code and get detailed explanations.")
    
    code_input = st.text_area(
        "📝 Paste your code:",
        placeholder="Paste code to explain...",
        height=200,
        key="explain_input"
    )
    
    language = st.selectbox("🔧 Language:", ["Python", "JavaScript", "Java", "C++"], key="explain_lang")
    
    col1, col2 = st.columns(2)
    with col1:
        detail_level = st.selectbox(
            "Detail Level:",
            ["Beginner", "Intermediate", "Advanced"],
            key="explain_detail"
        )
    with col2:
        focus_area = st.text_input("Focus on (optional):", key="explain_focus")
    
    if st.button("📖 Explain Code", use_container_width=True, key="explain_submit"):
        if not code_input.strip():
            st.error("Please paste code")
            st.stop()
        
        explanation_ph = st.empty()
        
        explain_prompt = f"""Explain this {language} code at {detail_level} level:

CODE:
```
{code_input}
```

Focus: {focus_area if focus_area else 'Overall explanation'}

Provide:
1. What it does (high level)
2. Key components breakdown
3. How it works (step by step)
4. Time/Space complexity (if applicable)
5. Common use cases
6. Potential improvements

Explain clearly for a {detail_level.lower()} programmer."""
        
        explanation = stream_response_with_web(explanation_ph, explain_prompt, {}, include_web_search=True, search_query=f"{language} {focus_area}")
        add_to_history("assistant", explanation, "Explain - Code")
        
        show_disclaimer()

# ==================== SEARCH SECTION ====================
elif section == " Search":
    st.subheader(" Search - Web-Based Code Solutions")
    st.markdown("Search the web for code solutions and best practices.")
    
    search_query = st.text_area(
        "🔍 What do you want to find?",
        placeholder="Example: How to implement binary search in Python",
        height=100,
        key="search_input"
    )
    
    language = st.selectbox("🔧 Language (optional):", ["Any", "Python", "JavaScript", "Java", "C++"], key="search_lang")
    
    if st.button("🌐 Search Web", use_container_width=True, key="search_submit"):
        if not search_query.strip():
            st.error("Please enter search query")
            st.stop()
        
        full_query = f"{search_query} {language}" if language != "Any" else search_query
        
        st.subheader("🔍 Search Results")
        with st.spinner("Searching..."):
            search_result = tavily_search(full_query)
            
            if search_result.get("success"):
                st.markdown(search_result.get("answer", "No results"))
                
                if search_result.get("sources"):
                    with st.expander("📚 Sources"):
                        st.markdown(search_result.get("sources"))
                
                add_to_history("assistant", search_result.get("answer", ""), "Search - Results")
            else:
                st.error(f"Search failed: {search_result.get('error')}")
        
        show_disclaimer()

# ==================== ASK SECTION ====================
elif section == " Ask":
    st.subheader(" Ask - General AI Assistance")
    st.markdown("Ask anything about coding, programming concepts, or development.")
    
    question = st.text_area(
        "❓ Your question:",
        placeholder="Ask anything about code, programming, or development...",
        height=150,
        key="ask_input"
    )
    
    include_web = st.checkbox("🌐 Include web search", value=True, key="ask_web")
    
    if st.button("💬 Get Answer", use_container_width=True, key="ask_submit"):
        if not question.strip():
            st.error("Please enter a question")
            st.stop()
        
        answer_ph = st.empty()
        
        answer_prompt = f"""Answer this programming question comprehensively:

{question}

Provide:
1. Direct answer
2. Explanation
3. Code examples if applicable
4. Best practices
5. Common pitfalls

Be thorough and practical."""
        
        answer = stream_response_with_web(
            answer_ph,
            answer_prompt,
            {},
            include_web_search=include_web,
            search_query=question if include_web else None
        )
        
        add_to_history("assistant", answer, "Ask - Answer")
        
        show_disclaimer()

# ==================== FOOTER ====================
st.markdown("---")
st.markdown("""
<div style='text-align: center; padding: 20px; color: #999;'>
    <p>⚡ Sorus AI - Your Coding Assistant</p>
    
</div>
""", unsafe_allow_html=True)
