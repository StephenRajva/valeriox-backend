import streamlit as st
import requests
import json
import pandas as pd
from io import StringIO
from PIL import Image # For handling image display

# --- Configuration ---
API_BASE_URL ="http://127.0.0.1:8080"
LOGO_PATH = "/Applications/PostgreSQL 18/api_project/.streamlit/logo.png" # Path to your Valeriox logo
PORTAL_NAME = "Valeriox" # Your chosen portal name
PORTAL_SLOGAN = "AI-Integrated Command & Control" # Your slogan

# --- Helper Functions ---
def fetch_data(endpoint):
    try:
        response = requests.get(f"{API_BASE_URL}/{endpoint}")
        response.raise_for_status() 
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Could not connect to API: {API_BASE_URL}/{endpoint}. Ensure the main_portal.py server is running.")
        return None

def post_query_to_ai(question):
    headers = {"Content-Type": "application/json"}
    payload = {"question": question}
    try:
        response = requests.post(f"{API_BASE_URL}/ask-ai", headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"❌ AI connection failed. Check server logs.")
        return {"answer": "AI system unreachable."}

# --- Streamlit Application Layout ---
st.set_page_config(layout="wide", page_title=f"{PORTAL_NAME} Portal", initial_sidebar_state="expanded")

# Custom styling for the logo and title in the sidebar
st.markdown(
    f"""
    <style>
        .css-e3g6js {{
            padding-top: 1rem;
            padding-bottom: 1rem;
        }}
        .st-emotion-cache-1na2gyc {{ /* Streamlit's class for the sidebar header */
            background-color: #29325D; /* Match secondaryBackgroundColor for sidebar */
            padding: 1.5rem 1rem;
            border-bottom: 1px solid #4A90E2; /* Subtle blue separator */
            display: flex;
            align-items: center;
            justify-content: center;
            flex-direction: column;
            color: #F0F2F6;
        }}
        .st-emotion-cache-1na2gyc img {{
            max-width: 150px;
            margin-bottom: 10px;
        }}
        .st-emotion-cache-1na2gyc .css-1aum1wu {{ /* Streamlit's class for the h1/h2 in sidebar */
            color: #F0F2F6 !important;
            font-size: 1.5em;
            margin: 0;
        }}
        .st-emotion-cache-1na2gyc .css-1q8dd3e {{ /* Streamlit's class for smaller text in sidebar */
            color: #A0B0D0 !important;
            font-size: 0.8em;
            margin-top: 5px;
        }}
        /* Ensure the main content area has the right background */
        .st-emotion-cache-z5fcl4 {{ /* Main content block */
            background-color: #1E2749; /* Match backgroundColor */
        }}
        /* Header for sections */
        h2 {{
            color: #4A90E2; /* Use primary color for section headers */
            border-bottom: 1px solid rgba(74, 144, 226, 0.3); /* Lighter blue line */
            padding-bottom: 0.5rem;
            margin-top: 2rem;
        }}
        /* Chat messages */
        .st-chat-message-user > div[data-testid="stChatMessageContent"] p {{
            color: #F0F2F6;
        }}
        .st-chat-message-assistant > div[data-testid="stChatMessageContent"] p {{
            color: #A0B0D0;
        }}
        /* General text */
        p {{
            color: #F0F2F6;
        }}
        /* For the dataframes */
        .stDataFrame {{
            border: 1px solid #4A90E2; /* Blue border for dataframes */
            border-radius: 5px;
        }}
    </style>
    """, 
    unsafe_allow_html=True
)

# Sidebar for logo and static info
with st.sidebar:
    try:
        logo = Image.open(LOGO_PATH)
        st.image(logo, use_column_width=True)
    except FileNotFoundError:
        st.error("Logo not found. Ensure logo.png is in the project directory.")
    st.markdown(f"## {PORTAL_NAME}")
    st.markdown(f"**{PORTAL_SLOGAN}**")
    st.markdown("---")
    st.write("API Status:")
    st.success(f"Backend: {API_BASE_URL} (Running)") # Placeholder, could ping API for real status
    st.markdown("---")
    st.info("💡 Morning Vibe: Clean, Focused, Data-Driven.")


st.title(f"{PORTAL_NAME} Portal Dashboard")
st.markdown("### Seamlessly Integrating HR, Finance, & Project Management")

# --- 1. AI Decision Assistant Section ---
st.header("🤖 AI Decision Assistant")
st.caption("Ask natural language questions to gain instant insights from your unified database.")

if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": f"Welcome to {PORTAL_NAME}, General Manager. I have access to all HR, Finance, and PM data. How can I assist you today?"}]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input("Ask a question (e.g., 'Which employee is blocked and why?', 'What is the total budget for the E-commerce UPI Integration project?'):"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    with st.spinner("Valeriox AI is analyzing the database and generating SQL..."):
        ai_response = post_query_to_ai(prompt)
        ai_answer = ai_response.get("answer", "System Error: Could not get response.")
        st.session_state.messages.append({"role": "assistant", "content": ai_answer})
        st.chat_message("assistant").write(ai_answer)

st.markdown("---")

# --- 2. Live Blocked Task Report Section ---
st.header("🛑 Live Blocked Task Report")
st.caption("Auto-generated report showing cross-departmental bottlenecks in real-time.")

report_data = fetch_data("reports/blocked-tasks")

if report_data:
    df = pd.DataFrame(report_data)

    df_display = df.rename(columns={
        "project_name": "Project",
        "task_name": "Task",
        "employee_name": "Assigned Employee",
        "employee_role": "Employee Role",
        "blocker_notes": "Blocker Details",
        "blocked_expense_vendor": "Blocked Expense Vendor",
        "blocked_expense_status": "Blocked Expense Status (Finance)"
    })

    df_display = df_display.drop(columns=['task_id', 'blocked_expense_id', 'status'])

    st.dataframe(df_display, use_container_width=True, hide_index=True)
else:
    st.warning("Blocked tasks report not loaded. Ensure your main_portal.py server is running on port 8080.")