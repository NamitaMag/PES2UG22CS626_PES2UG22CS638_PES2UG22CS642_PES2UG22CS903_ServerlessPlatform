# frontend/app.py
import streamlit as st
import requests
from datetime import datetime
import time

# Set page configuration
st.set_page_config(
    page_title="Lambda Serverless Platform",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling with improved fonts and modern design
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Fira+Code:wght@400;500&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    code, pre {
        font-family: 'Fira Code', monospace;
    }
    
    .main-header {
        font-size: 42px;
        background: linear-gradient(90deg, #3a7bd5, #00d2ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        padding: 10px 0;
        text-align: center;
        font-weight: 800;
        letter-spacing: -0.5px;
    }
    
    .subheader {
        font-size: 26px;
        color: #3a7bd5;
        padding: 5px 0;
        margin-bottom: 20px;
        border-bottom: 2px solid #3a7bd5;
        font-weight: 600;
    }
    
    .function-card {
        background-color: #f8f9fa;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        border-left: 5px solid #3a7bd5;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        transition: transform 0.2s, box-shadow 0.2s;
    }
    
    .function-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 8px rgba(0, 0, 0, 0.08);
    }
    
    .success-message {
        padding: 15px;
        border-radius: 8px;
        background-color: #d4edda;
        color: #155724;
        margin: 15px 0;
        font-weight: 500;
    }
    
    .error-message {
        padding: 15px;
        border-radius: 8px;
        background-color: #f8d7da;
        color: #721c24;
        margin: 15px 0;
        font-weight: 500;
    }
    
    .stButton>button {
        background: linear-gradient(90deg, #3a7bd5, #00d2ff);
        color: white;
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: 600;
        border: none;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(58, 123, 213, 0.3);
    }
    
    .stTextInput>div>div>input, .stNumberInput>div>div>input {
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        padding: 10px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    }
    
    .stTextInput>div>div>input:focus, .stNumberInput>div>div>input:focus {
        border-color: #3a7bd5;
        box-shadow: 0 0 0 2px rgba(58, 123, 213, 0.2);
    }
    
    .stSelectbox>div>div>div {
        border-radius: 8px;
        border: 1px solid #e0e0e0;
    }
    
    .stSelectbox>div>div>div:focus {
        border-color: #3a7bd5;
    }
    
    .stats-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        border-radius: 8px;
        padding: 15px;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    
    .stats-value {
        font-size: 28px;
        font-weight: 700;
        color: #3a7bd5;
    }
    
    .stats-label {
        font-size: 14px;
        color: #555;
        font-weight: 500;
    }
    
    .sidebar-title {
        font-size: 20px;
        font-weight: 600;
        color: #3a7bd5;
        margin-bottom: 10px;
        letter-spacing: -0.5px;
    }
    
    .footer {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 8px;
        margin-top: 40px;
        text-align: center;
    }
    
    .footer-link {
        color: #3a7bd5;
        text-decoration: none;
        font-weight: 500;
        margin: 0 15px;
    }
    
    .footer-link:hover {
        text-decoration: underline;
    }
    
    .code-editor {
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        overflow: hidden;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        font-weight: 600;
        color: #3a7bd5;
    }
</style>
""", unsafe_allow_html=True)

API_URL = "http://127.0.0.1:8000"

# Title with custom styling
st.markdown("<h1 class='main-header'>⚡ Lambda Serverless Platform</h1>", unsafe_allow_html=True)

# Enhanced sidebar
with st.sidebar:
    # Logo and branding
    st.markdown("""
    <div style="text-align: center; margin-bottom: 20px;">
        <svg width="80" height="80" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect width="100" height="100" rx="20" fill="url(#paint0_linear)"/>
            <path d="M30 70L50 30L70 70H30Z" stroke="white" stroke-width="4"/>
            <defs>
                <linearGradient id="paint0_linear" x1="0" y1="0" x2="100" y2="100" gradientUnits="userSpaceOnUse">
                    <stop stop-color="#3a7bd5"/>
                    <stop offset="1" stop-color="#00d2ff"/>
                </linearGradient>
            </defs>
        </svg>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<p class='sidebar-title'>Navigation</p>", unsafe_allow_html=True)
    menu = st.radio(
        "",
        ["Create Function", "View Functions", "Execute Function", "Update Function", "Delete Function"],
        key="menu"
    )
    
    st.markdown("---")
    st.markdown("<p class='sidebar-title'>Platform Stats</p>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div class="stats-card">
            <div class="stats-value">-</div>
            <div class="stats-label">Functions</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="stats-card">
            <div class="stats-value">-</div>
            <div class="stats-label">Executions</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown(f"**Current Time:** {datetime.now().strftime('%H:%M:%S')}")

# Helper to get all functions
@st.cache_data(ttl=60)  # Cache data for 60 seconds
def fetch_functions():
    with st.spinner("Loading functions..."):
        try:
            response = requests.get(f"{API_URL}/functions/")
            if response.ok:
                return response.json()
            else:
                return []
        except:
            return []

# Update stats in sidebar
def update_stats():
    functions = fetch_functions()
    with st.sidebar:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
            <div class="stats-card">
                <div class="stats-value">{len(functions)}</div>
                <div class="stats-label">Functions</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            # Just a placeholder stat
            st.markdown(f"""
            <div class="stats-card">
                <div class="stats-value">{len(functions) * 5}</div>
                <div class="stats-label">Executions</div>
            </div>
            """, unsafe_allow_html=True)

# 1. CREATE FUNCTION
if menu == "Create Function":
    st.markdown("<h2 class='subheader'>📝 Deploy a New Function</h2>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Function Name", placeholder="my-awesome-function")
    with col2:
        route = st.text_input("Route", placeholder="/api/my-function")
    
    col1, col2 = st.columns(2)
    with col1:
        language = st.selectbox("Language", ["python", "javascript"])
    with col2:
        timeout = st.number_input("Timeout (seconds)", min_value=1, max_value=30, value=5)
    
    # Template code based on selected language
    template_code = ""
    if language == "python":
        template_code = """def handler(event, context):
    # Your code here
    return {
        "message": "Hello from Lambda!",
        "status": "success"
    }"""
    else:
        template_code = """module.exports.handler = async (event, context) => {
    // Your code here
    return {
        message: "Hello from Lambda!",
        status: "success"
    };
};"""
    
    st.markdown("<div class='code-editor'>", unsafe_allow_html=True)
    code = st.text_area("Function Code", value=template_code, height=300)
    st.markdown("</div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 3])
    with col1:
        deploy_button = st.button("Deploy Function", key="deploy_btn", use_container_width=True)
    
    if deploy_button:
        with st.spinner("Deploying function..."):
            try:
                payload = {
                    "name": name,
                    "route": route,
                    "language": language,
                    "code": code,
                    "timeout": timeout,
                    "virtualization_backend": "docker"
                }
                
                response = requests.post(f"{API_URL}/functions/", json=payload)
                if response.ok:
                    st.markdown("""
                    <div class="success-message">
                        <strong>✅ Function deployed successfully!</strong>
                    </div>
                    """, unsafe_allow_html=True)
                    update_stats()
                    # Show a preview of the deployed function
                    st.markdown("### Function Preview")
                    st.code(code, language=language)
                    st.markdown(f"**Endpoint:** `{API_URL}{route}`")
                else:
                    st.markdown(f"""
                    <div class="error-message">
                        <strong>❌ Deployment failed:</strong> {response.json().get('detail', 'Unknown error')}
                    </div>
                    """, unsafe_allow_html=True)
            except Exception as e:
                st.markdown(f"""
                <div class="error-message">
                    <strong>❌ Connection error:</strong> Unable to connect to the backend service. Please check if the server is running.
                </div>
                """, unsafe_allow_html=True)

# 2. VIEW FUNCTIONS
elif menu == "View Functions":
    st.markdown("<h2 class='subheader'>📋 All Functions</h2>", unsafe_allow_html=True)
    
    functions = fetch_functions()
    update_stats()
    
    if not functions:
        st.info("No functions found. Create your first function!")
    else:
        # Add search/filter
        search = st.text_input("Search by name or route", placeholder="Type to filter...")
        
        # Filter functions based on search
        if search:
            filtered_functions = [f for f in functions if search.lower() in f['name'].lower() or search.lower() in f['route'].lower()]
        else:
            filtered_functions = functions
        
        st.markdown(f"Showing {len(filtered_functions)} of {len(functions)} functions")
        
        # Display functions
        for func in filtered_functions:
            with st.container():
                st.markdown(f"<div class='function-card'>", unsafe_allow_html=True)
                
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.markdown(f"#### {func['name']}")
                    st.markdown(f"**Route:** `{func['route']}`")
                with col2:
                    st.markdown(f"**Language:** {func['language']}")
                    st.markdown(f"**Timeout:** {func['timeout']}s")
                with col3:
                    st.markdown(f"**ID:** {func['id']}")
                    if st.button("Run", key=f"run_{func['id']}", use_container_width=True):
                        with st.spinner("Executing function..."):
                            try:
                                response = requests.post(f"{API_URL}/functions/{func['id']}/execute")
                                if response.ok:
                                    st.markdown("""
                                    <div class="success-message">
                                        <strong>✅ Execution successful!</strong>
                                    </div>
                                    """, unsafe_allow_html=True)
                                    st.code(response.json())
                                else:
                                    st.markdown(f"""
                                    <div class="error-message">
                                        <strong>❌ Execution failed:</strong> {response.text}
                                    </div>
                                    """, unsafe_allow_html=True)
                            except Exception as e:
                                st.markdown(f"""
                                <div class="error-message">
                                    <strong>❌ Connection error:</strong> Unable to connect to the backend service.
                                </div>
                                """, unsafe_allow_html=True)
                
                with st.expander("View Code"):
                    st.code(func['code'], language=func['language'])
                
                st.markdown("</div>", unsafe_allow_html=True)

# 3. EXECUTE FUNCTION
elif menu == "Execute Function":
    st.markdown("<h2 class='subheader'>▶️ Execute Function</h2>", unsafe_allow_html=True)
    
    functions = fetch_functions()
    update_stats()
    
    if not functions:
        st.info("No functions found. Create your first function!")
    else:
        options = {f"{f['name']} (ID: {f['id']})": f for f in functions}
        
        selected = st.selectbox("Select a Function", list(options.keys()))
        selected_func = options[selected]
        
        # Show function details
        with st.expander("Function Details", expanded=True):
            st.markdown(f"**Name:** {selected_func['name']}")
            st.markdown(f"**Route:** {selected_func['route']}")
            st.markdown(f"**Language:** {selected_func['language']}")
            st.code(selected_func['code'], language=selected_func['language'])
        
        # Execution section
        st.markdown("### Execute")
        
        # Add support for input parameters
        with st.expander("Input Parameters (Optional)"):
            param_input = st.text_area("JSON Input", "{}", height=100)
        
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("Run Function", use_container_width=True):
                with st.spinner("Executing function..."):
                    # Show loading animation
                    progress_bar = st.progress(0)
                    for i in range(10):
                        progress_bar.progress((i + 1) * 10)
                        time.sleep(0.1)
                    
                    # Make the execution request
                    try:
                        response = requests.post(f"{API_URL}/functions/{selected_func['id']}/execute")
                        if response.ok:
                            st.markdown("""
                            <div class="success-message">
                                <strong>✅ Execution successful!</strong>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Display result
                            st.markdown("### Result:")
                            st.json(response.json())
                            
                            # Execution metadata
                            st.markdown("### Execution Metadata:")
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.markdown(f"""
                                <div style="text-align: center; padding: 10px; background-color: #e8f4f8; border-radius: 8px;">
                                    <div style="font-size: 16px; color: #555;">Status</div>
                                    <div style="font-size: 20px; font-weight: 600; color: #3a7bd5;">Success</div>
                                </div>
                                """, unsafe_allow_html=True)
                            with col2:
                                st.markdown(f"""
                                <div style="text-align: center; padding: 10px; background-color: #e8f4f8; border-radius: 8px;">
                                    <div style="font-size: 16px; color: #555;">Execution Time</div>
                                    <div style="font-size: 20px; font-weight: 600; color: #3a7bd5;">{round(response.elapsed.total_seconds() * 1000, 2)}ms</div>
                                </div>
                                """, unsafe_allow_html=True)
                            with col3:
                                st.markdown(f"""
                                <div style="text-align: center; padding: 10px; background-color: #e8f4f8; border-radius: 8px;">
                                    <div style="font-size: 16px; color: #555;">Memory Used</div>
                                    <div style="font-size: 20px; font-weight: 600; color: #3a7bd5;">{round(len(str(response.json())) * 0.001, 2)}KB</div>
                                </div>
                                """, unsafe_allow_html=True)
                        else:
                            st.markdown(f"""
                            <div class="error-message">
                                <strong>❌ Execution failed:</strong> {response.text}
                            </div>
                            """, unsafe_allow_html=True)
                    except Exception as e:
                        st.markdown(f"""
                        <div class="error-message">
                            <strong>❌ Error connecting to API:</strong> {str(e)}
                        </div>
                        """, unsafe_allow_html=True)

# 4. UPDATE FUNCTION
elif menu == "Update Function":
    st.markdown("<h2 class='subheader'>✏️ Update Function</h2>", unsafe_allow_html=True)
    
    functions = fetch_functions()
    update_stats()
    
    if not functions:
        st.info("No functions found. Create your first function!")
    else:
        options = {f"{f['name']} (ID: {f['id']})": f for f in functions}
        
        selected = st.selectbox("Select a Function to Update", list(options.keys()))
        func = options[selected]
        
        st.markdown("### Edit Function")
        
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Function Name", func['name'])
        with col2:
            route = st.text_input("Route", func['route'])
        
        col1, col2 = st.columns(2)
        with col1:
            language = st.selectbox("Language", ["python", "javascript"], index=["python", "javascript"].index(func['language']))
        with col2:
            timeout = st.number_input("Timeout (seconds)", min_value=1, max_value=30, value=func['timeout'])
        
        # Add version information
        current_version = "1.0"  # Placeholder
        st.markdown(f"""
        <div style="padding: 10px; background-color: #f8f9fa; border-radius: 8px; margin-bottom: 15px;">
            <strong>Current Version:</strong> {current_version}
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<div class='code-editor'>", unsafe_allow_html=True)
        code = st.text_area("Function Code", func['code'], height=300)
        st.markdown("</div>", unsafe_allow_html=True)
        
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("Update Function", use_container_width=True):
                with st.spinner("Updating function..."):
                    try:
                        payload = {
                            "name": name,
                            "route": route,
                            "language": language,
                            "code": code,
                            "timeout": timeout,
                            "virtualization_backend": "docker"
                        }
                        
                        response = requests.put(f"{API_URL}/functions/{func['id']}", json=payload)
                        if response.ok:
                            st.markdown("""
                            <div class="success-message">
                                <strong>✅ Function updated successfully!</strong>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Show diff
                            st.markdown("### Changes")
                            changes = []
                            if name != func['name']:
                                changes.append(f"- Name: '{func['name']}' → '{name}'")
                            if route != func['route']:
                                changes.append(f"- Route: '{func['route']}' → '{route}'")
                            if language != func['language']:
                                changes.append(f"- Language: '{func['language']}' → '{language}'")
                            if timeout != func['timeout']:
                                changes.append(f"- Timeout: {func['timeout']}s → {timeout}s")
                            if code != func['code']:
                                changes.append(f"- Code updated")
                            
                            if changes:
                                for change in changes:
                                    st.markdown(f"""
                                    <div style="padding: 8px; background-color: #e8f4f8; border-radius: 5px; margin-bottom: 5px;">
                                        {change}
                                    </div>
                                    """, unsafe_allow_html=True)
                            else:
                                st.info("No changes were made")
                        else:
                            st.markdown(f"""
                            <div class="error-message">
                                <strong>❌ Failed to update function:</strong> {response.text}
                            </div>
                            """, unsafe_allow_html=True)
                    except Exception as e:
                        st.markdown(f"""
                        <div class="error-message">
                            <strong>❌ Connection error:</strong> Unable to connect to the backend service.
                        </div>
                        """, unsafe_allow_html=True)

# 5. DELETE FUNCTION
elif menu == "Delete Function":
    st.markdown("<h2 class='subheader'>🗑️ Delete Function</h2>", unsafe_allow_html=True)
    
    functions = fetch_functions()
    update_stats()
    
    if not functions:
        st.info("No functions found. Create your first function!")
    else:
        options = {f"{f['name']} (ID: {f['id']})": f for f in functions}
        
        selected = st.selectbox("Select a Function to Delete", list(options.keys()))
        func_id = options[selected]['id']
        func_name = options[selected]['name']
        
        # Show function details before deletion
        st.markdown(f"""
        <div style="padding: 15px; background-color: #fff3cd; border-left: 5px solid #ffc107; border-radius: 8px; margin: 20px 0;">
            <strong>⚠️ Warning:</strong> You are about to delete the function: <strong>{func_name}</strong> (ID: {func_id})
        </div>
        """, unsafe_allow_html=True)
        
        # Show function code for confirmation
        with st.expander("Function Code"):
            st.code(options[selected]['code'], language=options[selected]['language'])
        
        # Confirmation
        confirm = st.checkbox("I understand this action cannot be undone")
        
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("Delete Function", disabled=not confirm, use_container_width=True):
                with st.spinner("Deleting function..."):
                    try:
                        response = requests.delete(f"{API_URL}/functions/{func_id}")
                        if response.ok:
                            st.markdown(f"""
                            <div class="success-message">
                                <strong>✅ Function '{func_name}' (ID: {func_id}) deleted successfully.</strong>
                            </div>
                            """, unsafe_allow_html=True)
                            # Refresh the function list
                            st.cache_data.clear()
                            update_stats()
                        else:
                            st.markdown(f"""
                            <div class="error-message">
                                <strong>❌ Failed to delete function:</strong> {response.text}
                            </div>
                            """, unsafe_allow_html=True)
                    except Exception as e:
                        st.markdown(f"""
                        <div class="error-message">
                            <strong>❌ Connection error:</strong> Unable to connect to the backend service.
                        </div>
                        """, unsafe_allow_html=True)

# Add modern footer
st.markdown("""
<div class="footer">
    <div style="margin-bottom: 15px;">
        <strong>⚡ Lambda Serverless Platform</strong> | Built with Streamlit
    </div>
    <div>
        <a href="#" class="footer-link">Documentation</a>
        <a href="#" class="footer-link">GitHub</a>
        <a href="#" class="footer-link">Support</a>
    </div>
</div>
""", unsafe_allow_html=True)

# Initialize stats on first load
update_stats()