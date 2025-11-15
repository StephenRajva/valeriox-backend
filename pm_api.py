from typing import Optional, List
import psycopg2
from fastapi import FastAPI
from pydantic import BaseModel

# --- Configuration ---
# IMPORTANT: Replace 'YOUR_PASSWORD' with your PostgreSQL password
# Make sure to URL-encode any special characters (like '@' -> '%40')
#
# Notice we are connecting to the 'pm_db' this time
DB_CONNECT = "postgresql://postgres:Mothermary%402209@localhost:5432/pm_db"

# We will run this on port 8002
app = FastAPI()

# --- Pydantic Models ---
class ProjectTask(BaseModel):
    id: int
    project_id: int
    assignee_id: int
    task_name: str
    status: str
    blocker_notes: Optional[str] # Use Optional[str] for Python 3.9

# --- Database Connection ---
def get_db_connection():
    """Establishes a connection to the database and returns it."""
    try:
        conn = psycopg2.connect(DB_CONNECT)
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

# --- API Endpoints ---
@app.get("/")
def read_root():
    return {"status": "Project Management API is running"}

@app.get("/tasks", response_model=List[ProjectTask]) # Use List for Python 3.9
def get_all_tasks():
    """
    Fetches all tasks from the 'project_tasks' table.
    """
    conn = get_db_connection()
    if conn is None:
        return {"error": "Database connection failed"}
    
    with conn.cursor() as cursor:
        cursor.execute("SELECT id, project_id, assignee_id, task_name, status, blocker_notes FROM project_tasks")
        rows = cursor.fetchall()
    
    conn.close()
    
    # Manually convert tuples to dictionaries
    tasks = []
    for row in rows:
        tasks.append({
            "id": row[0],
            "project_id": row[1],
            "assignee_id": row[2],
            "task_name": row[3],
            "status": row[4],
            "blocker_notes": row[5]
        })
        
    return tasks