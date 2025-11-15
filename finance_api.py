from typing import Optional, List
import psycopg2
from fastapi import FastAPI
from pydantic import BaseModel
from datetime import date

# --- Configuration ---
# IMPORTANT: Replace 'YOUR_PASSWORD' with your PostgreSQL password
# Make sure to URL-encode any special characters (like '@' -> '%40')
#
# Notice we are connecting to the 'finance_db' this time
DB_CONNECT = "postgresql://postgres:Mothermary%402209@localhost:5432/finance_db"

# We will run this on port 8001
app = FastAPI()

# --- Pydantic Models ---
class Project(BaseModel):
    id: int
    name: str
    total_budget: float

class Expense(BaseModel):
    id: int
    project_id: int
    vendor: Optional[str] # | None means the field can be null
    description: Optional[str]
    amount: float
    status: str
    date: date

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
    return {"status": "Finance API is running"}

@app.get("/projects", response_model=List[Project])
def get_all_projects():
    """
    Fetches all projects from the 'projects' table.
    """
    conn = get_db_connection()
    if conn is None:
        return {"error": "Database connection failed"}
    
    with conn.cursor() as cursor:
        cursor.execute("SELECT id, name, total_budget FROM projects")
        rows = cursor.fetchall()
    
    conn.close()
    
    # Manually convert tuples to dictionaries
    projects = []
    for row in rows:
        projects.append({
            "id": row[0],
            "name": row[1],
            "total_budget": row[2]
        })
        
    return projects

@app.get("/expenses", response_model=List[Expense])
def get_all_expenses():
    """
    Fetches all expenses from the 'expenses' table.
    """
    conn = get_db_connection()
    if conn is None:
        return {"error": "Database connection failed"}
    
    with conn.cursor() as cursor:
        cursor.execute("SELECT id, project_id, vendor, description, amount, status, date FROM expenses")
        rows = cursor.fetchall()
    
    conn.close()
    
    # Manually convert tuples to dictionaries
    expenses = []
    for row in rows:
        expenses.append({
            "id": row[0],
            "project_id": row[1],
            "vendor": row[2],
            "description": row[3],
            "amount": row[4],
            "status": row[5],
            "date": row[6]
        })
        
    return expenses