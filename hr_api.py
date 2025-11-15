import psycopg2
from fastapi import FastAPI
from pydantic import BaseModel
from datetime import date

# --- Configuration ---
# This is the connection string for your HR database
# Format: "postgresql://USERNAME:PASSWORD@localhost:5432/DATABASE_NAME"
#
# IMPORTANT: Replace 'YOUR_PASSWORD' with the password you created 
# when you installed PostgreSQL.
DB_CONNECT = "postgresql://postgres:Mothermary%402209@localhost:5432/hr_db"

app = FastAPI()

# --- Pydantic Models ---
# These models define the *shape* of the data we expect to send/receive.
# This provides automatic data validation.

class Employee(BaseModel):
    id: int
    name: str
    role: str
    department: str

class Timesheet(BaseModel):
    id: int
    employee_id: int
    project_id: int
    hours_logged: float  # Use float for numeric(5,2)
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
# These are the "links" our application will create.

@app.get("/")
def read_root():
    """A simple 'hello' endpoint to test if the API is running."""
    return {"status": "HR API is running"}


@app.get("/employees", response_model=list[Employee])
def get_all_employees():
    """
    Fetches all employees from the 'employees' table.
    """
    conn = get_db_connection()
    if conn is None:
        return {"error": "Database connection failed"}
    
    # Use a default cursor
    with conn.cursor() as cursor:
        cursor.execute("SELECT id, name, role, department FROM employees")
        rows = cursor.fetchall()  # This gets a list of tuples
    
    conn.close()
    
    # --- THIS IS THE FIX ---
    # Manually convert the list of tuples into a list of dictionaries
    employees = []
    for row in rows:
        employees.append({
            "id": row[0],
            "name": row[1],
            "role": row[2],
            "department": row[3]
        })
        
    return employees  # Return the new list of dictionaries


@app.get("/timesheets", response_model=list[Timesheet])
def get_all_timesheets():
    """
    Fetches all timesheet records from the 'timesheets' table.
    """
    conn = get_db_connection()
    if conn is None:
        return {"error": "Database connection failed"}
    
    # Use a default cursor
    with conn.cursor() as cursor:
        cursor.execute("SELECT id, employee_id, project_id, hours_logged, date FROM timesheets")
        rows = cursor.fetchall()
    
    conn.close()
    
    # --- THIS IS THE FIX ---
    # Manually convert the list of tuples into a list of dictionaries
    timesheets = []
    for row in rows:
        timesheets.append({
            "id": row[0],
            "employee_id": row[1],
            "project_id": row[2],
            "hours_logged": row[3],
            "date": row[4]
        })
        
    return timesheets  # Return the new list of dictionaries