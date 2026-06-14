import os
import streamlit as st
from pathlib import Path
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from datetime import datetime
import requests

# ==================== PAGE SETUP ====================
st.set_page_config(
    page_title="Sorus AI",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== CSS STYLING ====================
st.markdown("""
<style>
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 10px 20px !important;
        font-weight: 600 !important;
    }

    .stButton > button:hover {
        transform: translateY(-2px) !important;
    }

    .stTextArea textarea {
        border: 2px solid #667eea !important;
        border-radius: 8px !important;
        padding: 12px !important;
    }

    .stTextInput input {
        border: 2px solid #667eea !important;
        border-radius: 8px !important;
        padding: 10px !important;
    }

    .response-box {
        background: rgba(102, 126, 234, 0.05);
        border-left: 4px solid #667eea;
        padding: 16px;
        border-radius: 8px;
        margin: 12px 0;
    }
</style>
""", unsafe_allow_html=True)

# ==================== SETUP API KEYS ====================
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", os.getenv("GROQ_API_KEY"))
TAVILY_API_KEY = st.secrets.get("TAVILY_API_KEY", os.getenv("TAVILY_API_KEY"))

if not GROQ_API_KEY:
    st.error("❌ Please set GROQ_API_KEY in .streamlit/secrets.toml")
    st.stop()

# Initialize LLM
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.7,
    api_key=GROQ_API_KEY
)

# Create folder for saving code
Path("generated_code").mkdir(exist_ok=True)

# ==================== SESSION STATE ====================
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "generated_files" not in st.session_state:
    st.session_state.generated_files = []

# ==================== WEB SEARCH FUNCTION ====================
def tavily_search(query):
    """Search the web using Tavily API"""
    if not TAVILY_API_KEY:
        return {"success": False, "error": "Web search not configured"}
   
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
            answer = data.get("answer", "No answer found")
            results = data.get("results", [])
           
            sources_text = ""
            for i, result in enumerate(results[:3], 1):
                sources_text += f"\n{i}. [{result.get('title', 'No title')}]({result.get('url', '#')})"
           
            return {
                "success": True,
                "answer": answer,
                "sources": sources_text,
                "results": results
            }
        else:
            return {"success": False, "error": f"API Error: {response.status_code}"}
           
    except Exception as e:
        return {"success": False, "error": str(e)}

# ==================== HELPER FUNCTIONS ====================
def run_chain(template, variables):
    """Run LLM chain and return response"""
    try:
        prompt = PromptTemplate.from_template(template)
        chain = prompt | llm
        response = chain.invoke(variables if variables else {})
        return response.content if hasattr(response, 'content') else str(response)
    except Exception as e:
        return f"❌ Error: {str(e)}"

def stream_response(placeholder, template, variables, search_query=None):
    """Stream response from LLM with optional web search"""
    web_context = ""
    sources_display = ""
   
    # Add web search if requested and API key exists
    if search_query and TAVILY_API_KEY:
        with st.spinner("🔍 Searching the web..."):
            search_result = tavily_search(search_query)
            if search_result.get("success"):
                web_answer = search_result.get("answer", "")
                sources = search_result.get("sources", "")
                web_context = f"\n\n[WEB SEARCH RESULTS]\n{web_answer}"
                sources_display = sources
   
    # Update template with web context
    enhanced_template = template + web_context if web_context else template
   
    full_response = ""
   
    try:
        prompt = PromptTemplate.from_template(enhanced_template)
        chain = prompt | llm
        
        for chunk in chain.stream(variables if variables else {}):
            if hasattr(chunk, 'content'):
                full_response += chunk.content
            else:
                full_response += str(chunk)
            placeholder.markdown(full_response + "▌")
       
        placeholder.markdown(full_response)
    except Exception as e:
        placeholder.error(f"Error: {str(e)}")
        full_response = f"Error: {str(e)}"
   
    # Show sources if available
    if sources_display:
        st.markdown("### 📚 Sources Used:")
        st.markdown(sources_display)
   
    return full_response

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

def add_to_history(role, content):
    """Add message to chat history"""
    st.session_state.chat_history.append({
        "role": role,
        "content": content[:100] + "..." if len(content) > 100 else content,
        "full_content": content,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
    })

# ==================== SIDEBAR ====================
st.sidebar.title("⚡ Sorus AI")
st.sidebar.markdown("---")

sections = ["🚀 Build", "🐛 Debug", "🧪 Test", "⚡ Optimize", "📖 Explain", "🔍 Search", "❓ Ask"]

section = st.sidebar.selectbox("Choose what you want to do:", sections)

st.sidebar.markdown("---")

# Buttons for managing chat
col1, col2 = st.sidebar.columns(2)
with col1:
    if st.button("🔄 New Chat", use_container_width=True):
        st.session_state.chat_history = []
        st.session_state.generated_files = []
        st.rerun()

with col2:
    if st.button("🗑️ Clear All", use_container_width=True):
        st.session_state.chat_history = []
        st.session_state.generated_files = []
        st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("### 💬 Chat History")

if st.session_state.chat_history:
    for item in st.session_state.chat_history:
        emoji = "👤" if item["role"] == "user" else "🤖"
        st.sidebar.markdown(f"""
        **{emoji} {item['role'].upper()}** ({item['timestamp']})
        
        {item['content']}
        """)
else:
    st.sidebar.markdown("*No chat history yet*")

st.sidebar.markdown("---")
st.sidebar.markdown("### 💾 Generated Files")

if st.session_state.generated_files:
    for file in st.session_state.generated_files:
        st.sidebar.markdown(f"📄 **{file['name']}** ({file['timestamp']})")
else:
    st.sidebar.markdown("*No files generated yet*")

# ==================== MAIN TITLE ====================
st.title("⚡ Sorus AI - Your Coding Assistant")
st.markdown("💡 **Note:** AI can make mistakes. Always review and test the code before using it!")
st.markdown("---")

# ==================== BUILD SECTION ====================
if section == "🚀 Build":
    st.subheader("🚀 Build - Generate Code")
    st.markdown("Tell us what code you want to build. We'll generate it for you!")
    
    # Input form
    requirement = st.text_area(
        "What do you want to build?",
        placeholder="Example: A Python function to check if a number is prime",
        height=120,
        key="build_input"
    )
    
    col1, col2, col3 = st.columns(3)
    with col1:
        language = st.selectbox("Programming Language:", ["Python", "JavaScript", "Java", "C++"], key="build_lang")
    with col2:
        use_web = st.checkbox("Search web for best practices?", value=True, key="build_web")
    with col3:
        st.write("")  # Spacing
    
    if st.button("🚀 Generate Code", use_container_width=True, key="build_btn"):
        if not requirement.strip():
            st.error("❌ Please describe what you want to build!")
        else:
            # Show what we're doing
            st.info("📝 Generating code for you...")
            
            # Generate code
            code_placeholder = st.empty()
            
            search_query = f"{requirement} {language} best practices" if use_web else None
            
            code_prompt = f"""Generate a complete, working {language} solution for:

{requirement}

Requirements:
- Include all necessary code
- Add comments explaining what it does
- Include at least one example of how to use it
- Handle errors properly
- Make it beginner-friendly

Return ONLY the complete code, nothing else."""
            
            full_code = stream_response(
                code_placeholder,
                code_prompt,
                {},
                search_query=search_query
            )
            
            add_to_history("assistant", full_code)
            
            # Save and copy buttons
            st.markdown("---")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                filename = st.text_input("Save as (filename only):", value="my_code", key="build_filename")
            
            with col2:
                if st.button("💾 Save Code", use_container_width=True, key="build_save"):
                    if filename:
                        path = save_code(filename, full_code, language)
                        st.success(f"✅ Saved to: `{path}`")
                    else:
                        st.error("❌ Enter a filename!")
            
            with col3:
                if st.button("📋 Copy Code", use_container_width=True, key="build_copy"):
                    st.code(full_code, language=language.lower())
    
    # Input box stays here for next use
    st.markdown("---")
    st.markdown("💡 **Tip:** The input box above stays here. You can generate more code anytime!")

# ==================== DEBUG SECTION ====================
elif section == "🐛 Debug":
    st.subheader("🐛 Debug - Fix Broken Code")
    st.markdown("Paste code that has bugs. We'll find and fix them!")
    
    code_input = st.text_area(
        "Paste your buggy code here:",
        placeholder="Paste the code with errors...",
        height=200,
        key="debug_code"
    )
    
    language = st.selectbox("Programming Language:", ["Python", "JavaScript", "Java", "C++"], key="debug_lang")
    
    error_msg = st.text_input("What error are you getting? (optional):", key="debug_error")
    
    if st.button("🔍 Find & Fix Bugs", use_container_width=True, key="debug_btn"):
        if not code_input.strip():
            st.error("❌ Please paste some code!")
        else:
            # Find issues
            st.info("🔍 Analyzing code...")
            
            issues_ph = st.empty()
            issues_prompt = f"""Find ALL bugs and problems in this {language} code:

```
{code_input}
```

Error message: {error_msg if error_msg else 'None'}

List each bug with:
1. What's wrong
2. Where (line number if possible)
3. How to fix it"""
            
            issues = run_chain(issues_prompt, {})
            issues_ph.markdown("### 🐛 Issues Found:\n" + issues)
            add_to_history("assistant", issues)
            
            st.markdown("---")
            
            # Generate fixed code
            st.info("✅ Generating fixed code...")
            fixed_ph = st.empty()
            
            fixed_prompt = f"""Fix ALL bugs in this {language} code:

```
{code_input}
```

Return ONLY the complete fixed code, nothing else."""
            
            fixed_code = stream_response(fixed_ph, fixed_prompt, {})
            add_to_history("assistant", fixed_code)
            
            # Save options
            st.markdown("---")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("💾 Save Fixed Code", use_container_width=True, key="debug_save"):
                    name = st.text_input("Filename:", value="fixed_code", key="debug_fname")
                    if name:
                        path = save_code(name, fixed_code, language)
                        st.success(f"✅ Saved!")
            
            with col2:
                if st.button("📋 Show Fixed Code", use_container_width=True, key="debug_show"):
                    st.code(fixed_code, language=language.lower())
    
    st.markdown("---")
    st.markdown("💡 **Tip:** Paste new code anytime to debug it!")

# ==================== TEST SECTION ====================
elif section == "🧪 Test":
    st.subheader("🧪 Test - Generate Test Cases")
    st.markdown("Paste code and get test cases to check if it works!")
    
    code_input = st.text_area(
        "Paste your code here:",
        placeholder="Paste code to test...",
        height=200,
        key="test_code"
    )
    
    language = st.selectbox("Programming Language:", ["Python", "JavaScript", "Java", "C++"], key="test_lang")
    
    framework = st.text_input("Test framework (e.g., pytest, jest, junit):", value="pytest", key="test_framework")
    
    if st.button("🧪 Generate Tests", use_container_width=True, key="test_btn"):
        if not code_input.strip():
            st.error("❌ Please paste some code!")
        else:
            st.info("📝 Generating test cases...")
            
            tests_ph = st.empty()
            tests_prompt = f"""Generate complete {framework} test cases for this {language} code:

```
{code_input}
```

Requirements:
- Test all the main functions
- Test edge cases (empty inputs, zero, negative numbers, etc.)
- Test error handling
- Make tests clear and easy to understand
- Include comments explaining what each test does

Return ONLY the complete test code."""
            
            tests_code = stream_response(tests_ph, tests_prompt, {})
            add_to_history("assistant", tests_code)
            
            # Save options
            st.markdown("---")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("💾 Save Tests", use_container_width=True, key="test_save"):
                    name = st.text_input("Filename:", value="test_code", key="test_fname")
                    if name:
                        path = save_code(name, tests_code, language)
                        st.success(f"✅ Saved!")
            
            with col2:
                if st.button("📋 Show Tests", use_container_width=True, key="test_show"):
                    st.code(tests_code, language=language.lower())
    
    st.markdown("---")
    st.markdown("💡 **Tip:** Tests help make sure your code works correctly!")

# ==================== OPTIMIZE SECTION ====================
elif section == "⚡ Optimize":
    st.subheader("⚡ Optimize - Make Code Faster")
    st.markdown("Paste code and we'll suggest ways to make it faster!")
    
    code_input = st.text_area(
        "Paste your code here:",
        placeholder="Paste code to optimize...",
        height=200,
        key="opt_code"
    )
    
    language = st.selectbox("Programming Language:", ["Python", "JavaScript", "Java", "C++"], key="opt_lang")
    
    goal = st.selectbox(
        "What's most important?",
        ["Speed (faster)", "Memory (use less RAM)", "Readability (easy to understand)"],
        key="opt_goal"
    )
    
    if st.button("⚡ Optimize Code", use_container_width=True, key="opt_btn"):
        if not code_input.strip():
            st.error("❌ Please paste some code!")
        else:
            st.info("📊 Analyzing code...")
            
            # Analyze
            analysis_ph = st.empty()
            analysis_prompt = f"""Analyze this {language} code and suggest optimizations for {goal}:

```
{code_input}
```

Explain:
1. What's slow/inefficient about the current code
2. Specific problems (if any)
3. How to make it better

Be clear and simple."""
            
            analysis = run_chain(analysis_prompt, {})
            analysis_ph.markdown("### 📊 Analysis:\n" + analysis)
            add_to_history("assistant", analysis)
            
            st.markdown("---")
            
            # Generate optimized code
            st.info("✨ Creating optimized version...")
            optimized_ph = st.empty()
            
            optimized_prompt = f"""Create an optimized version of this {language} code focused on {goal}:

```
{code_input}
```

Return ONLY the complete optimized code, nothing else."""
            
            optimized_code = stream_response(optimized_ph, optimized_prompt, {})
            add_to_history("assistant", optimized_code)
            
            # Save options
            st.markdown("---")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("💾 Save Optimized", use_container_width=True, key="opt_save"):
                    name = st.text_input("Filename:", value="optimized", key="opt_fname")
                    if name:
                        path = save_code(name, optimized_code, language)
                        st.success(f"✅ Saved!")
            
            with col2:
                if st.button("📋 Show Optimized", use_container_width=True, key="opt_show"):
                    st.code(optimized_code, language=language.lower())
    
    st.markdown("---")
    st.markdown("💡 **Tip:** Optimized code runs faster and uses less memory!")

# ==================== EXPLAIN SECTION ====================
elif section == "📖 Explain":
    st.subheader("📖 Explain - Understand Code")
    st.markdown("Paste code and we'll explain what it does!")
    
    code_input = st.text_area(
        "Paste your code here:",
        placeholder="Paste code to understand...",
        height=200,
        key="explain_code"
    )
    
    language = st.selectbox("Programming Language:", ["Python", "JavaScript", "Java", "C++"], key="explain_lang")
    
    level = st.selectbox(
        "Explain at what level?",
        ["Beginner (simple words)", "Intermediate (some technical terms)", "Advanced (detailed)"],
        key="explain_level"
    )
    
    if st.button("📖 Explain Code", use_container_width=True, key="explain_btn"):
        if not code_input.strip():
            st.error("❌ Please paste some code!")
        else:
            st.info("📝 Explaining code...")
            
            explanation_ph = st.empty()
            explain_prompt = f"""Explain this {language} code in {level}:

```
{code_input}
```

Explain:
1. What the code does (simple overview)
2. Each part and how it works
3. What it's useful for
4. Any important concepts to know

Use simple language, not too technical."""
            
            explanation = stream_response(
                explanation_ph,
                explain_prompt,
                {},
                search_query=f"{language} programming concepts"
            )
            
            add_to_history("assistant", explanation)
    
    st.markdown("---")
    st.markdown("💡 **Tip:** Understanding code helps you learn programming!")

# ==================== SEARCH SECTION ====================
elif section == "🔍 Search":
    st.subheader("🔍 Search - Find Code Solutions Online")
    st.markdown("Search the internet for code solutions!")
    
    search_input = st.text_area(
        "What do you want to find?",
        placeholder="Example: How to read a file in Python",
        height=100,
        key="search_query"
    )
    
    language = st.selectbox(
        "Programming Language (optional):",
        ["Any", "Python", "JavaScript", "Java", "C++"],
        key="search_lang"
    )
    
    if st.button("🌐 Search the Web", use_container_width=True, key="search_btn"):
        if not search_input.strip():
            st.error("❌ Please enter what you want to find!")
        else:
            st.info("🔍 Searching...")
            
            query = f"{search_input} {language}" if language != "Any" else search_input
            
            result_ph = st.empty()
            
            search_result = tavily_search(query)
            
            if search_result.get("success"):
                result_ph.markdown("### 🔍 Results:\n" + search_result.get("answer", "No results"))
                add_to_history("assistant", search_result.get("answer", ""))
                
                if search_result.get("sources"):
                    st.markdown("### 📚 Helpful Links:")
                    st.markdown(search_result.get("sources"))
            else:
                st.error(f"❌ Search failed: {search_result.get('error')}")
    
    st.markdown("---")
    st.markdown("💡 **Tip:** Web search helps you find real-world solutions!")

# ==================== ASK SECTION ====================
elif section == "❓ Ask":
    st.subheader("❓ Ask - General Questions")
    st.markdown("Ask anything about coding and programming!")
    
    question = st.text_area(
        "Your question:",
        placeholder="Ask anything about programming, code, or development...",
        height=150,
        key="ask_input"
    )
    
    use_web = st.checkbox("Search the web for answers?", value=True, key="ask_web")
    
    if st.button("💬 Get Answer", use_container_width=True, key="ask_btn"):
        if not question.strip():
            st.error("❌ Please ask a question!")
        else:
            st.info("💭 Thinking...")
            
            answer_ph = st.empty()
            answer_prompt = f"""Answer this programming question:

{question}

Provide:
1. A clear answer
2. Why that's the answer
3. An example if helpful
4. Any tips or best practices

Keep it simple and beginner-friendly."""
            
            answer = stream_response(
                answer_ph,
                answer_prompt,
                {},
                search_query=question if use_web else None
            )
            
            add_to_history("assistant", answer)
    
    st.markdown("---")
    st.markdown("💡 **Tip:** Don't be shy to ask! Learning is how you get better!")

# ==================== FOOTER ====================
st.markdown("---")
st.markdown("""
<div style='text-align: center; padding: 20px; color: #999;'>
    <p>⚡ <strong>Sorus AI</strong> - Your Coding Assistant</p>
    <p>Always review AI-generated code before using it!</p>
</div>
""", unsafe_allow_html=True)
