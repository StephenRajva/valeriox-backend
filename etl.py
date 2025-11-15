import psycopg2
import requests
from typing import Optional, List
from pydantic import BaseModel, Field

# --- Configuration ---
# IMPORTANT: Replace 'YOUR_PASSWORD' with your PostgreSQL password
# Make sure to URL-encode any special characters (like '@' -> '%40')
#
# Notice we are connecting to the 'unified_db' this time
DB_CONNECT = "postgresql://postgres:Mothermary%402209@localhost:5432/unified_db"

# --- Pydantic Models for Data Validation ---
# These models match the JSON we expect from our APIs

class Employee(BaseModel):
    id: int
    name: str
    role: str
    department: str

class Project(BaseModel):
    id: int
    name: str
    total_budget: float

class Expense(BaseModel):
    id: int
    project_id: int
    vendor: Optional[str]
    description: Optional[str]
    amount: float
    status: str
    date: str # Keep as string for now, simplifies insertion

class ProjectTask(BaseModel):
    id: int
    project_id: int
    assignee_id: int
    task_name: str
    status: str
    blocker_notes: Optional[str]

# --- Database Setup Function ---
def create_unified_tables(conn):
    """
    Creates all the new tables in the unified database.
    This DROPS existing tables, so it's fresh every time.
    """
    with conn.cursor() as cursor:
        # We add 'source_api' to know where the data came from
        cursor.execute("""
        DROP TABLE IF EXISTS unified_tasks;
        DROP TABLE IF EXISTS unified_timesheets;
        DROP TABLE IF EXISTS unified_expenses;
        DROP TABLE IF EXISTS unified_projects;
        DROP TABLE IF EXISTS unified_employees;
        
        CREATE TABLE unified_employees (
            id INTEGER PRIMARY KEY,
            name VARCHAR(100),
            role VARCHAR(100),
            department VARCHAR(50),
            source_api VARCHAR(20)
        );
        
        CREATE TABLE unified_projects (
            id INTEGER PRIMARY KEY,
            name VARCHAR(100),
            total_budget NUMERIC(12, 2),
            source_api VARCHAR(20)
        );
        
        CREATE TABLE unified_expenses (
            id INTEGER PRIMARY KEY,
            project_id INTEGER REFERENCES unified_projects(id),
            vendor VARCHAR(100),
            description VARCHAR(255),
            amount NUMERIC(10, 2),
            status VARCHAR(20),
            date DATE,
            source_api VARCHAR(20)
        );
        
        CREATE TABLE unified_tasks (
            id INTEGER PRIMARY KEY,
            project_id INTEGER REFERENCES unified_projects(id),
            assignee_id INTEGER REFERENCES unified_employees(id),
            task_name VARCHAR(255),
            status VARCHAR(20),
            blocker_notes TEXT,
            source_api VARCHAR(20)
        );
        
        -- We won't create a timesheet table for now to keep the demo simple
        -- We can add it later if needed
        """)
    conn.commit() # Save the changes
    print("✅ Unified tables created successfully.")

# --- ETL (Extract, Transform, Load) Functions ---

def fetch_data(api_url: str, model: BaseModel) -> List[dict]:
    """Fetches data from an API and validates it."""
    try:
        response = requests.get(api_url)
        response.raise_for_status() # Raise an error for bad responses (404, 500)
        
        # Validate data
        data = response.json()
        validated_data = [model.model_validate(item) for item in data]
        # Convert Pydantic models back to dictionaries for insertion
        return [item.model_dump() for item in validated_data]

    except requests.exceptions.RequestException as e:
        print(f"❌ ERROR fetching {api_url}: {e}")
        return []
    except Exception as e:
        print(f"❌ ERROR validating data from {api_url}: {e}")
        return []

def run_etl():
    """Main ETL function to run the whole process."""
    print("--- Starting ETL Process ---")
    
    # 1. EXTRACT: Fetch data from all 3 running APIs
    print("Fetching data from APIs...")
    employees_data = fetch_data("http://127.0.0.1:8000/employees", Employee)
    projects_data = fetch_data("http://127.0.0.1:8001/projects", Project)
    expenses_data = fetch_data("http://127.0.0.1:8001/expenses", Expense)
    tasks_data = fetch_data("http://127.0.0.1:8002/tasks", ProjectTask)
    
    if not all([employees_data, projects_data, expenses_data, tasks_data]):
        print("❌ One or more APIs failed to return data. Stopping ETL.")
        return

    print("Data fetched successfully.")
    
    # 2. TRANSFORM & 3. LOAD
    # Connect to the unified database
    try:
        conn = psycopg2.connect(DB_CONNECT)
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return

    # Create the tables (fresh every time)
    create_unified_tables(conn)
    
    # Load data into new unified tables
    with conn.cursor() as cursor:
        print("Loading data into 'unified_employees'...")
        for emp in employees_data:
            cursor.execute(
                """INSERT INTO unified_employees (id, name, role, department, source_api) 
                   VALUES (%s, %s, %s, %s, %s)""",
                (emp['id'], emp['name'], emp['role'], emp['department'], 'hr_api')
            )
        
        print("Loading data into 'unified_projects'...")
        for proj in projects_data:
            cursor.execute(
                """INSERT INTO unified_projects (id, name, total_budget, source_api) 
                   VALUES (%s, %s, %s, %s)""",
                (proj['id'], proj['name'], proj['total_budget'], 'finance_api')
            )
        
        print("Loading data into 'unified_expenses'...")
        for exp in expenses_data:
            cursor.execute(
                """INSERT INTO unified_expenses (id, project_id, vendor, description, amount, status, date, source_api) 
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                (exp['id'], exp['project_id'], exp['vendor'], exp['description'], exp['amount'], exp['status'], exp['date'], 'finance_api')
            )
            
        print("Loading data into 'unified_tasks'...")
        for task in tasks_data:
            cursor.execute(
                """INSERT INTO unified_tasks (id, project_id, assignee_id, task_name, status, blocker_notes, source_api) 
                   VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                (task['id'], task['project_id'], task['assignee_id'], task['task_name'], task['status'], task['blocker_notes'], 'pm_api')
            )

    # Save all changes to the database
    conn.commit()
    conn.close()
    
    print("--- 🚀 ETL Process Complete ---")
    print("Your 'unified_db' now has all the data!")

# --- This makes the script runnable ---
if __name__ == "__main__":
    run_etl()