# frontend/app.py
import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000"

st.title("Lambda Serverless Platform 🚀")

menu = st.sidebar.radio("Choose an option", ["Create Function", "View Functions", "Execute Function", "Update Function", "Delete Function"])

# Helper to get all functions
def fetch_functions():
    response = requests.get(f"{API_URL}/functions/")
    if response.ok:
        return response.json()
    else:
        st.error("Error fetching functions.")
        return []

# 1. CREATE FUNCTION
if menu == "Create Function":
    st.header("📝 Deploy a New Function")
    name = st.text_input("Function Name")
    route = st.text_input("Route")
    language = st.selectbox("Language", ["python", "javascript"])
    code = st.text_area("Function Code", height=200)
    timeout = st.number_input("Timeout (seconds)", value=5)

    if st.button("Deploy"):
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
            st.success("Function deployed successfully!")
        else:
            st.error(response.json()['detail'])

# 2. VIEW FUNCTIONS
elif menu == "View Functions":
    st.header("📋 All Functions")
    functions = fetch_functions()
    for func in functions:
        st.code(func['code'], language=func['language'])
        st.write(f"**ID**: {func['id']} | **Name**: {func['name']} | **Route**: {func['route']} | **Timeout**: {func['timeout']}s | **Language**: {func['language']}")
        st.markdown("---")

# 3. EXECUTE FUNCTION
elif menu == "Execute Function":
    st.header("▶️ Execute Function")
    functions = fetch_functions()
    options = {f"{f['name']} (ID: {f['id']})": f['id'] for f in functions}

    selected = st.selectbox("Select a Function", list(options.keys()))
    if st.button("Run"):
        func_id = options[selected]
        response = requests.post(f"{API_URL}/functions/{func_id}/execute")
        if response.ok:
            st.success("Execution Output:")
            st.code(response.json())
        else:
            st.error("Execution failed: " + response.text)

# 4. UPDATE FUNCTION
elif menu == "Update Function":
    st.header("✏️ Update Function")
    functions = fetch_functions()
    options = {f"{f['name']} (ID: {f['id']})": f for f in functions}

    selected = st.selectbox("Select a Function", list(options.keys()))
    func = options[selected]

    name = st.text_input("Function Name", func['name'])
    route = st.text_input("Route", func['route'])
    language = st.selectbox("Language", ["python", "javascript"], index=["python", "javascript"].index(func['language']))
    code = st.text_area("Function Code", func['code'], height=200)
    timeout = st.number_input("Timeout (seconds)", value=func['timeout'])

    if st.button("Update"):
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
            st.success("Function updated successfully!")
        else:
            st.error("Failed to update function")

# 5. DELETE FUNCTION
elif menu == "Delete Function":
    st.header("🗑️ Delete Function")
    functions = fetch_functions()
    options = {f"{f['name']} (ID: {f['id']})": f['id'] for f in functions}

    selected = st.selectbox("Select a Function", list(options.keys()))
    if st.button("Delete"):
        func_id = options[selected]
        response = requests.delete(f"{API_URL}/functions/{func_id}")
        if response.ok:
            st.success(f"Function ID {func_id} deleted.")
        else:
            st.error("Failed to delete function")
