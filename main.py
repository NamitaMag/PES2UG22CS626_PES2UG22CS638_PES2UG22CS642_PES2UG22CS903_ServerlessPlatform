from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import sqlite3
from engine import run_function  # Importing the enhanced engine.py

app = FastAPI(title="Lambda Serverless Platform")

DB_PATH = 'lambda_platform.db'

# Pydantic models
class FunctionCreate(BaseModel):
    name: str
    route: str
    language: str
    code: str
    timeout: int = 5
    virtualization_backend: str

class Function(FunctionCreate):
    id: int
    is_active: bool

class ExecuteRequest(BaseModel):
    payload: dict = {}

# Utility function to connect to DB
def get_db():
    return sqlite3.connect(DB_PATH)

# -------------------------
# CRUD Endpoints
# -------------------------

@app.post("/functions/", response_model=Function)
def create_function(function: FunctionCreate):
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO functions (name, route, language, code, timeout, virtualization_backend)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (function.name, function.route, function.language, function.code, function.timeout, function.virtualization_backend))
        conn.commit()
        func_id = cursor.lastrowid
        return {**function.dict(), "id": func_id, "is_active": True}
    except sqlite3.IntegrityError as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()

@app.get("/functions/", response_model=List[Function])
def list_functions():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM functions")
    rows = cursor.fetchall()
    conn.close()
    return [Function(id=row[0], name=row[1], route=row[2], language=row[3], code=row[4],
                     timeout=row[5], virtualization_backend=row[6], is_active=bool(row[7])) for row in rows]

@app.get("/functions/{func_id}", response_model=Function)
def get_function(func_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM functions WHERE id=?", (func_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return Function(id=row[0], name=row[1], route=row[2], language=row[3], code=row[4],
                        timeout=row[5], virtualization_backend=row[6], is_active=bool(row[7]))
    raise HTTPException(status_code=404, detail="Function not found")

@app.put("/functions/{func_id}", response_model=Function)
def update_function(func_id: int, function: FunctionCreate):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE functions
        SET name=?, route=?, language=?, code=?, timeout=?, virtualization_backend=?, updated_at=CURRENT_TIMESTAMP
        WHERE id=?
    """, (function.name, function.route, function.language, function.code, function.timeout, function.virtualization_backend, func_id))
    conn.commit()
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Function not found")
    conn.close()
    return {**function.dict(), "id": func_id, "is_active": True}

@app.delete("/functions/{func_id}")
def delete_function(func_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM functions WHERE id=?", (func_id,))
    conn.commit()
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Function not found")
    conn.close()
    return {"message": f"Function {func_id} deleted"}

# -------------------------
# Execution Endpoint
# -------------------------

@app.post("/execute/{route}")
def execute_function(route: str, request: ExecuteRequest):
    """
    Executes a function based on the provided route and payload.
    It ensures that the function is pre-warmed and uses a container pool for better performance.
    """
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM functions WHERE route=? AND is_active=1", (route,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Function with given route not found or inactive")

    func = {
        "id": row[0],
        "name": row[1],
        "route": row[2],
        "language": row[3],
        "code": row[4],
        "timeout": row[5],
        "virtualization_backend": row[6]
    }

    try:
        output = run_function(language=func["language"], code=func["code"], input_payload=request.payload, timeout=func["timeout"], route=func["route"], virtualization_backend=func["virtualization_backend"])
        if output["success"]:
            return output["result"]
        else:
            raise HTTPException(status_code=500, detail=output["error"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

