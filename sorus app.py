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

# ==================== CSS ====================
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
    .stTextArea textarea, .stTextInput input {
        border: 2px solid #667eea !important;
        border-radius: 8px !important;
    }
    .web-result {
        background: rgba(52, 152, 219, 0.05);
        border-left: 4px solid #3498db;
        padding: 12px;
        margin: 12px 0;
        border-radius: 6px;
    }
    .followup-response {
        background: rgba(46, 204, 113, 0.05);
        border-left: 4px solid #27ae60;
        padding: 15px;
        margin: 15px 0;
        border-radius: 6px;
    }
</style>
""", unsafe_allow_html=True)

# ==================== API SETUP ====================
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", os.getenv("GROQ_API_KEY"))
TAVILY_API_KEY = st.secrets.get("TAVILY_API_KEY", os.getenv("TAVILY_API_KEY"))

if not GROQ_API_KEY:
    st.error("❌ Please set GROQ_API_KEY")
    st.stop()

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.7,
    api_key=GROQ_API_KEY
)

Path("generated_code").mkdir(exist_ok=True)

# ==================== SESSION STATE ====================
if "build_code" not in st.session_state:
    st.session_state.build_code = None
if "explain_code_content" not in st.session_state:
    st.session_state.explain_code_content = None
if "ask_response" not in st.session_state:
    st.session_state.ask_response = None

# ==================== WEB SEARCH ====================
def web_search(query):
    """Search web using Tavily API"""
    if not TAVILY_API_KEY:
        st.warning("⚠️ Tavily API key not set. Web search disabled.")
        return None
    
    try:
        url = "https://api.tavily.com/search"
        payload = {
            "api_key": TAVILY_API_KEY,
            "query": query,
            "include_answer": True,
            "max_results": 5,
            "search_depth": "advanced"
        }
        
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return {
                "answer": data.get("answer", ""),
                "results": data.get("results", []),
                "success": True
            }
        else:
            st.warning(f"⚠️ Web search API returned error: {response.status_code}")
            return None
    except Exception as e:
        st.warning(f"⚠️ Web search error: {str(e)}")
        return None

def format_sources(results):
    """Format search results as sources"""
    if not results:
        return ""
    sources = "\n### 📚 Sources:\n"
    for i, r in enumerate(results[:3], 1):
        title = r.get('title', 'Link')
        url = r.get('url', '#')
        sources += f"{i}. [{title}]({url})\n"
    return sources

# ==================== LLM FUNCTIONS ====================
def run_chain(template, variables):
    """Run LLM chain (non-streaming) - displays result directly"""
    try:
        prompt = PromptTemplate.from_template(template)
        chain = prompt | llm
        response = chain.invoke(variables if variables else {})
        result = response.content if hasattr(response, 'content') else str(response)
        st.markdown(result)
        return result
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        return f"Error: {str(e)}"

def stream_response(placeholder, template, variables):
    """Stream response from LLM"""
    try:
        prompt = PromptTemplate.from_template(template)
        chain = prompt | llm
        full_response = ""
        
        for chunk in chain.stream(variables if variables else {}):
            if hasattr(chunk, 'content'):
                full_response += chunk.content
            else:
                full_response += str(chunk)
            placeholder.markdown(full_response + "▌")
        
        placeholder.markdown(full_response)
        return full_response
    except Exception as e:
        placeholder.error(f"❌ Error: {str(e)}")
        return f"Error: {str(e)}"

def save_code(filename, code, language):
    """Save code to file"""
    ext = {"python": "py", "javascript": "js", "java": "java", "cpp": "cpp"}.get(language.lower(), "txt")
    path = f"generated_code/{filename}.{ext}"
    with open(path, "w") as f:
        f.write(code)
    st.success(f"✅ Saved to: {path}")
    return path

# ==================== SIDEBAR ====================
st.sidebar.title("⚡ Sorus AI")
st.sidebar.markdown("---")

sections = ["🚀 Build", "🐛 Debug", "🧪 Test", "⚡ Optimize", "📖 Explain", "❓ Ask"]
section = st.sidebar.selectbox("Choose Section:", sections)

st.sidebar.markdown("---")
st.sidebar.markdown("💡 **Note:** Review all AI-generated code before using!")

# ==================== MAIN TITLE ====================
st.title("⚡ Sorus AI - Coding Assistant")
st.markdown("---")

# ==================== BUILD SECTION (LIKE MANUS AI) ====================
if section == "🚀 Build":
    st.subheader("🚀 Build - Generate Code (Professional Flow)")
    
    requirement = st.text_area(
        "What do you want to build?",
        placeholder="Example: Create a Python function to sort a list using bubble sort with comments",
        height=120,
        key="build_req"
    )
    
    col1, col2, col3 = st.columns(3)
    with col1:
        language = st.selectbox("Language:", ["Python", "JavaScript", "Java", "C++"], key="build_lang")
    with col2:
        use_web = st.checkbox("🌐 Web Search", value=True, key="build_web")
    with col3:
        pass
    
    if st.button("🚀 Start Building", use_container_width=True, key="build_start"):
        if not requirement.strip():
            st.error("❌ Please describe what to build!")
            st.stop()
        
        st.session_state.build_code = None
        
        # ==================== PHASE 1: INFORMATION ====================
        st.markdown("### 📚 PHASE 1: Understanding Requirements")
        info_ph = st.empty()
        
        info_prompt = f"""Analyze this requirement and provide ONLY:

REQUIREMENT: {requirement}
LANGUAGE: {language}

Format exactly:
**KEY REQUIREMENTS:**
- Requirement 1
- Requirement 2

**EDGE CASES:**
- Edge case 1
- Edge case 2

**BEST PRACTICES:**
- Practice 1
- Practice 2

Be concise."""
        
        info = run_chain(info_prompt, {})
        info_ph.markdown(info)
        
        # ==================== PHASE 2: RESOURCES ====================
        st.markdown("### ⚙️ PHASE 2: Required Resources")
        res_ph = st.empty()
        
        res_prompt = f"""What resources are needed for this {language} code?

REQUIREMENT: {requirement}

Format exactly:
**DEPENDENCIES:**
- Dependency 1: why needed

**MEMORY/PERFORMANCE:**
- Requirement 1

**SETUP:**
- Setup step 1

Be minimal and practical."""
        
        resources = run_chain(res_prompt, {})
        res_ph.markdown(resources)
        
        # ==================== PHASE 3: WHAT TO DO ====================
        st.markdown("### 📋 PHASE 3: What We'll Do")
        what_ph = st.empty()
        
        what_prompt = f"""For this requirement, explain the approach:

REQUIREMENT: {requirement}
LANGUAGE: {language}

Format:
**APPROACH:**
Explain in 3-4 sentences what we'll do

**ALGORITHM/METHOD:**
- Step 1
- Step 2
- Step 3

**OUTPUT:**
What the final code will do"""
        
        what = run_chain(what_prompt, {})
        what_ph.markdown(what)
        
        # ==================== PHASE 4: TASKS ====================
        st.markdown("### ✅ PHASE 4: Implementation Tasks")
        tasks_ph = st.empty()
        
        tasks_prompt = f"""Break down the implementation into tasks:

REQUIREMENT: {requirement}
LANGUAGE: {language}

Format:
**TASK 1:** [name] - [description]
**TASK 2:** [name] - [description]
**TASK 3:** [name] - [description]
**TASK 4:** [name] - [description]

Each task should be specific and actionable."""
        
        tasks = run_chain(tasks_prompt, {})
        tasks_ph.markdown(tasks)
        
        # ==================== PHASE 5: WEB SEARCH ====================
        if use_web:
            st.markdown("### 🌐 PHASE 5: Best Practices from Web")
            
            with st.spinner("🔍 Searching for best practices..."):
                search_query = f"{language} {' '.join(requirement.split()[0:4])} best practices"
                st.info(f"🔍 Searching: '{search_query}'")
                
                search_result = web_search(search_query)
                
                if search_result and search_result.get("success"):
                    answer = search_result.get("answer", "")
                    results = search_result.get("results", [])
                    
                    if answer:
                        st.markdown(f"<div class='web-result'><strong>📚 Web Results:</strong>\n\n{answer}</div>", unsafe_allow_html=True)
                    
                    sources = format_sources(results)
                    if sources:
                        st.markdown(sources)
                    
                    st.success("✅ Web search completed!")
                else:
                    st.warning("⚠️ Web search did not return results. Proceeding with generation...")
        
        # ==================== PHASE 6: FINAL CODE (ONLY ONCE) ====================
        st.markdown("### 💾 PHASE 6: Final Production-Ready Code")
        code_ph = st.empty()
        
        code_prompt = f"""Generate ONE complete, production-ready {language} solution.

REQUIREMENT: {requirement}

MUST INCLUDE:
- All necessary imports at the top
- Comprehensive comments explaining each line
- Full error handling
- Type hints (if applicable)
- At least one example showing how to use it
- Handle edge cases
- Clean, readable code

Return ONLY the complete code - nothing else, no explanations."""
        
        final_code = stream_response(code_ph, code_prompt, {})
        st.session_state.build_code = final_code
        
        # ==================== SAVE OPTIONS ====================
        st.markdown("---")
        st.subheader("💾 Save Your Code")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            filename = st.text_input("Filename:", value="my_code", key="build_fname")
        with col2:
            if st.button("💾 Save", use_container_width=True, key="build_save"):
                if filename:
                    save_code(filename, final_code, language)
        with col3:
            if st.button("📋 Copy", use_container_width=True, key="build_copy"):
                st.code(final_code, language=language.lower())
    
    # ==================== FOLLOW-UP SECTION ====================
   st.markdown("---")
    if st.session_state.build_code:
    st.subheader("💬 Ask About This Code")
    followup = st.text_input(
        "What do you want to know about the generated code?",
        key="build_followup_input"
    )
    
    if followup and followup.strip():
        st.markdown("---")
        st.markdown("### 📝 Answer:")
        
        followup_prompt = f"""Answer this question about the code:
 
CODE:
```
{st.session_state.build_code.replace('{', '{{').replace('}', '}}')}
```
 
QUESTION: {followup}
 
Provide a clear, helpful answer."""
        
        run_chain(followup_prompt, {})
else:
    st.info("💡 Generate code first, then ask follow-up questions here!")
 
# ==================== DEBUG SECTION ====================
elif section == "🐛 Debug":
    st.subheader("🐛 Debug - Fix Broken Code")
    
    code_input = st.text_area("Paste buggy code:", placeholder="Paste code with errors...", height=200, key="debug_code")
    language = st.selectbox("Language:", ["Python", "JavaScript", "Java", "C++"], key="debug_lang")
    error_msg = st.text_input("Error message (optional):", key="debug_error")
    
    if st.button("🔍 Find & Fix Bugs", use_container_width=True, key="debug_start"):
        if not code_input.strip():
            st.error("❌ Paste some code!")
            st.stop()
        
        st.subheader("🐛 Issues Found")
        issues_ph = st.empty()
        
        issues_prompt = f"""Find ALL bugs in this {language} code:

```
{code_input}
```

Error: {error_msg if error_msg else 'None'}

List each bug:
1. **What's wrong:** [description]
2. **Where:** [line or location]
3. **Severity:** [Critical/High/Medium]
4. **How to fix:** [solution]"""
        
        issues = run_chain(issues_prompt, {})
        issues_ph.markdown(issues)
        
        st.subheader("✅ Fixed Code")
        fixed_ph = st.empty()
        
        fixed_prompt = f"""Fix ALL bugs in this {language} code:

```
{code_input}
```

Return ONLY the complete fixed code."""
        
        fixed_code = stream_response(fixed_ph, fixed_prompt, {})
        
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            fname = st.text_input("Save as:", value="fixed_code", key="debug_fname")
            if st.button("💾 Save", use_container_width=True, key="debug_save"):
                save_code(fname, fixed_code, language)
        with col2:
            if st.button("📋 Copy", use_container_width=True, key="debug_copy"):
                st.code(fixed_code, language=language.lower())

# ==================== TEST SECTION ====================
elif section == "🧪 Test":
    st.subheader("🧪 Test - Generate Test Cases")
    
    code_input = st.text_area("Paste code to test:", placeholder="Paste code...", height=200, key="test_code")
    language = st.selectbox("Language:", ["Python", "JavaScript", "Java", "C++"], key="test_lang")
    framework = st.text_input("Test framework:", value="pytest", key="test_framework")
    
    if st.button("🧪 Generate Tests", use_container_width=True, key="test_start"):
        if not code_input.strip():
            st.error("❌ Paste some code!")
            st.stop()
        
        st.subheader("📝 Test Cases")
        tests_ph = st.empty()
        
        tests_prompt = f"""Generate complete {framework} test cases for this {language} code:

```
{code_input}
```

Include:
- Normal case tests
- Edge case tests (empty, zero, negative, null, etc.)
- Error handling tests
- Clear comments
- Ready to run

Return ONLY complete test code."""
        
        tests_code = stream_response(tests_ph, tests_prompt, {})
        
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            fname = st.text_input("Save as:", value="tests", key="test_fname")
            if st.button("💾 Save", use_container_width=True, key="test_save"):
                save_code(fname, tests_code, language)
        with col2:
            if st.button("📋 Copy", use_container_width=True, key="test_copy"):
                st.code(tests_code, language=language.lower())

# ==================== OPTIMIZE SECTION ====================
elif section == "⚡ Optimize":
    st.subheader("⚡ Optimize - Make Code Faster")
    
    code_input = st.text_area("Paste code:", placeholder="Paste code to optimize...", height=200, key="opt_code")
    language = st.selectbox("Language:", ["Python", "JavaScript", "Java", "C++"], key="opt_lang")
    goal = st.selectbox("Optimize for:", ["Speed (faster)", "Memory (less RAM)", "Readability"], key="opt_goal")
    
    if st.button("⚡ Optimize", use_container_width=True, key="opt_start"):
        if not code_input.strip():
            st.error("❌ Paste some code!")
            st.stop()
        
        st.subheader("📊 Analysis")
        analysis_ph = st.empty()
        
        analysis_prompt = f"""Analyze this {language} code and suggest optimizations:

```
{code_input}
```

Optimize for: {goal}

Explain:
1. **Bottlenecks:** What's slow/inefficient
2. **Problems:** Specific issues
3. **Solutions:** How to improve
4. **Impact:** Expected improvement"""
        
        analysis = run_chain(analysis_prompt, {})
        analysis_ph.markdown(analysis)
        
        st.subheader("✨ Optimized Code")
        opt_ph = st.empty()
        
        opt_prompt = f"""Create optimized {language} code for {goal}:

```
{code_input}
```

Return ONLY complete optimized code."""
        
        opt_code = stream_response(opt_ph, opt_prompt, {})
        
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            fname = st.text_input("Save as:", value="optimized", key="opt_fname")
            if st.button("💾 Save", use_container_width=True, key="opt_save"):
                save_code(fname, opt_code, language)
        with col2:
            if st.button("📋 Copy", use_container_width=True, key="opt_copy"):
                st.code(opt_code, language=language.lower())

# ==================== EXPLAIN SECTION (LINE-BY-LINE) ====================
elif section == "📖 Explain":
    st.subheader("📖 Explain - Line-by-Line Code Explanation")
    
    code_input = st.text_area("Paste code to explain:", placeholder="Paste code...", height=200, key="explain_code")
    language = st.selectbox("Language:", ["Python", "JavaScript", "Java", "C++"], key="explain_lang")
    level = st.selectbox("Explain for:", ["Beginners", "Intermediate", "Advanced"], key="explain_level")
    
    if st.button("📖 Explain Each Line", use_container_width=True, key="explain_start"):
        if not code_input.strip():
            st.error("❌ Paste some code!")
            st.stop()
        
        st.session_state.explain_code_content = code_input
        
        st.subheader("📖 Line-by-Line Explanation")
        explain_ph = st.empty()
        
        explain_prompt = f"""Explain this {language} code line by line for {level}:

```
{code_input}
```

Format for EACH LINE OR GROUP OF RELATED LINES:

**Line X-Y:**
```
[show the actual code line]
```
**Explanation:** [explain what this line does in simple terms for {level}]
**Why:** [why is this important]

Go through the entire code. Be thorough and clear."""
        
        explanation = stream_response(explain_ph, explain_prompt, {})
        
        st.markdown("---")
        if st.checkbox("🌐 Add web best practices?", key="explain_web"):
            with st.spinner("🔍 Searching for best practices..."):
                search_query = f"{language} {code_input.split()[0:3]} best practices"
                search_result = web_search(search_query)
                
                if search_result and search_result.get("success"):
                    answer = search_result.get("answer", "")
                    results = search_result.get("results", [])
                    
                    st.markdown("### 💡 Best Practices from Web:")
                    if answer:
                        st.markdown(f"<div class='web-result'>{answer}</div>", unsafe_allow_html=True)
                    
                    sources = format_sources(results)
                    if sources:
                        st.markdown(sources)
    
    # ==================== FOLLOW-UP SECTION ====================
    st.markdown("---")
if st.session_state.explain_code_content:
    st.subheader("💬 Ask About This Code")
    followup = st.text_input("Ask a follow-up question about the code:", key="explain_followup_input")
    
    if followup and followup.strip():
        st.markdown("---")
        st.markdown("### 📝 Answer:")
        
        followup_prompt = f"""Answer this question about the code for {level}:
 
CODE:
```
{st.session_state.explain_code_content.replace('{', '{{').replace('}', '}}')}
```
 
QUESTION: {followup}
 
Give a clear, helpful answer suitable for {level}."""
        
        run_chain(followup_prompt, {})
else:
    st.info("💡 Explain code first, then ask follow-up questions!")
 
# ==================== ASK SECTION ====================
elif section == "❓ Ask":
    st.subheader("❓ Ask - Ask About Programming")
    
    question = st.text_area(
        "Your question:",
        placeholder="Ask anything about coding, programming, best practices, etc...",
        height=150,
        key="ask_input"
    )
    
    use_web = st.checkbox("🌐 Search web for answer?", value=True, key="ask_web")
    
    if st.button("💬 Get Answer", use_container_width=True, key="ask_start"):
        if not question.strip():
            st.error("❌ Ask a question!")
            st.stop()
        
        st.session_state.ask_response = question
        
        st.subheader("💡 Answer")
        answer_ph = st.empty()
        
        answer_prompt = f"""Answer this programming question:

{question}

Include:
1. **Direct Answer:** [clear answer]
2. **Explanation:** [why this is the answer]
3. **Code Example:** [if helpful]
4. **Best Practices:** [tips]
5. **Common Mistakes:** [what to avoid]

Be thorough and beginner-friendly."""
        
        answer = stream_response(answer_ph, answer_prompt, {})
        st.session_state.ask_response = answer
        
        # Web search
        if use_web:
            st.markdown("---")
            with st.spinner("🌐 Searching web for additional resources..."):
                search_result = web_search(question)
                
                if search_result and search_result.get("success"):
                    answer_text = search_result.get("answer", "")
                    results = search_result.get("results", [])
                    
                    st.markdown("### 📚 Additional Resources:")
                    if answer_text:
                        st.markdown(f"<div class='web-result'>{answer_text}</div>", unsafe_allow_html=True)
                    
                    sources = format_sources(results)
                    if sources:
                        st.markdown(sources)
    
    # ==================== FOLLOW-UP SECTION ====================
    st.markdown("---")
if st.session_state.ask_response:
    st.subheader("💬 Ask Follow-up Questions")
    followup = st.text_input("Ask another question or request clarification:", key="ask_followup_input")
    
    if followup and followup.strip():
        st.markdown("---")
        st.markdown("### 📝 Follow-up Answer:")
        
        followup_prompt = f"""Based on this previous answer:
 
{st.session_state.ask_response[:500].replace('{', '{{').replace('}', '}}')}...
 
Now answer this follow-up question:
 
{followup}
 
Be clear and helpful."""
        
        run_chain(followup_prompt, {})
else:
    st.info("💡 Ask a question first!")
# ==================== FOOTER ====================
st.markdown("---")
st.markdown("""
<div style='text-align: center; padding: 20px; color: #999;'>
    <p>⚡ <strong>Sorus AI</strong> - Your Coding Assistant</p>
    <p>Always review AI-generated code before using in production!</p>
</div>
""", unsafe_allow_html=True)
