from fastapi.middleware.cors import CORSMiddleware
import os
import psycopg2
from typing import Optional, List
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv

# --- New AI Imports ---
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_openai import ChatOpenAI  # <-- THIS IS NOW OPENAI
from langchain_community.agent_toolkits.sql.base import create_sql_agent 
from langchain_community.agent_toolkits import SQLDatabaseToolkit

# --- Load API Key ---
# This securely loads your OPENAI_API_KEY from the .env file
load_dotenv()

# --- Configuration ---
# IMPORTANT: Replace 'YOUR_PASSWORD' with your PostgreSQL password
DB_CONNECT_STRING = os.getenv("DATABASE_URL")

app = FastAPI()

# This gives permission to your frontend to connect
origins = ["*"]  # Allows all connections

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Allows GET and POST
    allow_headers=["*"],
)
# --- Initialize AI Components ---
try:
    # 1. Connect LangChain to our Unified Database
    db = SQLDatabase.from_uri(DB_CONNECT_STRING)

    # 2. Get the API key from the environment
    openai_api_key = os.getenv("OPENAI_API_KEY")
    
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY not found in .env file")

    # 3. Initialize the AI model (the "brain")
    #    We are now using OpenAI's GPT-3.5-turbo model
    llm = ChatOpenAI(
        model="gpt-3.5-turbo", # Reliable and fast for this task
        temperature=0, 
        openai_api_key=openai_api_key
    )

    # 4. Create the "Agent"
    toolkit = SQLDatabaseToolkit(db=db, llm=llm)
    # 5. Initialize the Agent with a mandatory System Prompt
    system_prompt = """
    You are an expert SQL analyst. Your purpose is to answer the user's question using the database.
    Your MOST IMPORTANT RULE: When asked about an employee being 'BLOCKED', you MUST run the query against the 'unified_tasks' table and filter for status = 'Blocked'.
    You must JOIN the 'unified_tasks' table with 'unified_employees' on 'assignee_id' to get the employee's name.
    NEVER use a non-existent column like 'blocked'.
    """
    
    agent_executor = create_sql_agent(
        llm=llm,
        toolkit=toolkit,
        verbose=True,
        # We pass the system prompt directly into the LLM config
        agent_kwargs={"system_prompt": system_prompt} 
    )
    print("✅ AI Agent Initialized Successfully (OpenAI).")
except Exception as e:
    print(f"❌ FAILED TO INITIALIZE AI AGENT: {e}")
    agent_executor = None

# --- Pydantic Models ---
class BlockedTaskReport(BaseModel):
    task_id: int
    task_name: str
    project_name: str
    employee_name: str
    employee_role: str
    status: str
    blocker_notes: str
    blocked_expense_id: int
    blocked_expense_vendor: str
    blocked_expense_status: str

# New model for the AI's input
class AIQuery(BaseModel):
    question: str

# --- Database Connection (for old report) ---
def get_db_connection():
    try:
        # We must URL-decode the password for psycopg2
        password = DB_CONNECT_STRING.split(':')[2].split('@')[0].replace("%40", "@")
        conn_string = f"postgresql://postgres:{password}@localhost:5432/unified_db"
        conn = psycopg2.connect(conn_string)
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

# --- API Endpoints ---
@app.get("/")
def read_root():
    return {"status": "AI-Assisted Unified Portal (powered by Google Gemini) is running"}

# --- THE "AI CHATBOT" ENDPOINT ---
# --- THE "AI CHATBOT" ENDPOINT ---
@app.post("/ask-ai")
def ask_ai_agent(query: AIQuery):
    if agent_executor is None:
        return {"question": query.question, "answer": "Error: AI Agent failed to initialize. Check API key and DB connection."}
        
    # --- THIS IS THE FIX ---
    # We add the necessary instructions directly to the input string.
    full_query = (
        "You are an expert SQL analyst. To find which employee is blocked "
        "and why, you MUST JOIN the 'unified_tasks' table with the "
        "'unified_employees' table. Filter the 'unified_tasks' status by 'Blocked'. "
        f"The user's question is: {query.question}"
    )
    
    print(f"--- AI Agent received question: {query.question} ---")
    try:
        # We call the agent with our new, instructional query
        result = agent_executor.invoke({"input": full_query})
        
        # The agent's final answer is in the 'output' key
        answer = result.get("output", "I'm sorry, I couldn't find an answer.")
        
        print(f"--- AI Agent response: {answer} ---")
        return {"question": query.question, "answer": answer}

    except Exception as e:
        print(f"--- AI Agent Error: {e} ---")
        return {"question": query.question, "answer": f"An error occurred: {e}"}
# --- THE "FIXED REPORT" ENDPOINT ---
@app.get("/reports/blocked-tasks", response_model=List[BlockedTaskReport])
def get_blocked_task_report():
    """
    This is the "smart" endpoint that runs our pre-built
    SQL query to find the *real* reason a task is blocked.
    """
    conn = get_db_connection()
    if conn is None:
        return {"error": "Database connection failed"}
    
    query = """
    SELECT 
        t.id AS task_id,
        t.task_name,
        p.name AS project_name,
        e.name AS employee_name,
        e.role AS employee_role,
        t.status,
        t.blocker_notes,
        ex.id AS blocked_expense_id,
        ex.vendor AS blocked_expense_vendor,
        ex.status AS blocked_expense_status
    FROM 
        unified_tasks t
    JOIN 
        unified_projects p ON t.project_id = p.id
    JOIN 
        unified_employees e ON t.assignee_id = e.id
    JOIN 
        unified_expenses ex ON t.project_id = ex.project_id
    WHERE 
        t.status = 'Blocked'
        AND t.blocker_notes LIKE 'Waiting for Expense ID ' || ex.id || '%';
    """
    
    with conn.cursor() as cursor:
        cursor.execute(query)
        rows = cursor.fetchall()
    
    conn.close()
    
    report = []
    for row in rows:
        report.append({
            "task_id": row[0],
            "task_name": row[1],
            "project_name": row[2],
            "employee_name": row[3],
            "employee_role": row[4],
            "status": row[5],
            "blocker_notes": row[6],
            "blocked_expense_id": row[7],
            "blocked_expense_vendor": row[8],
            "blocked_expense_status": row[9]
        })
        
    return report