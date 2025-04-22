from pathlib import Path
import shutil
import subprocess
import uuid
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import sqlite3
from datetime import datetime
from engine import run_function_in_docker, run_function_in_gvisor  # Make sure this import works
from database import get_runtime_backend, save_execution_metrics
import traceback
import threading
import time
from engine import container_pool
from metrics import router as metrics_router

app = FastAPI()

app.include_router(metrics_router)

from database import init_db
init_db()


SUPPORTED_LANGUAGES = {
    "python": {
        "filename": "function.py",
        "dockerfile": "Dockerfile.python",
        "image_name": "func-python"
    },
    "javascript": {
        "filename": "function.js",
        "dockerfile": "Dockerfile.node",
        "image_name": "func-node"
    }
}

FUNCTIONS_DIR = Path("functions")

app = FastAPI(title="Lambda Serverless Platform")

DB_PATH = 'lambda_platform.db'

# Pydantic models
class FunctionCreate(BaseModel):
    name: str
    route: str
    language: str
    code: str
    timeout: int = 5
    virtualization_backend: str = "docker"

class Function(FunctionCreate):
    id: int
    is_active: bool = True

# DB Utility
def get_db():
    return sqlite3.connect(DB_PATH)

def warm_up_container(image_name: str, dockerfile: str, code_filename: str, sample_code: str):
    """
    Warm up a container image by pre-building it.
    """
    warm_dir = FUNCTIONS_DIR / f"warmup_{uuid.uuid4().hex[:8]}"
    warm_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Validate dockerfile
        dockerfile_path = Path(dockerfile)
        if not dockerfile or not dockerfile_path.exists():
            raise ValueError(f"Dockerfile '{dockerfile}' not found or invalid.")

        # Write sample code
        with open(warm_dir / code_filename, "w") as f:
            f.write(sample_code)

        shutil.copy(dockerfile_path, warm_dir / "Dockerfile")

        subprocess.run(
            ["docker", "build", "-t", image_name, "."],
            cwd=warm_dir,
            check=True
        )

        container_pool[image_name] = True  # mark as warm

    except Exception as e:
        print(f"[Warm-up Error] {e}")
        container_pool[image_name] = False
    finally:
        shutil.rmtree(warm_dir, ignore_errors=True)


def async_warm_up(language: str):
    """
    Run warm-up in a background thread for async preloading
    """
    if language in SUPPORTED_LANGUAGES:
        config = SUPPORTED_LANGUAGES[language]
        image_name = config["image_name"]
        dockerfile = config["dockerfile"]
        code_filename = config["filename"]
        sample_code = "print('Warming up container...')" if language == "python" else "console.log('Warm-up');"

        threading.Thread(target=warm_up_container, args=(image_name, dockerfile, code_filename, sample_code)).start()

# ------------------------- CRUD Endpoints -------------------------

@app.post("/functions/{func_id}/execute")
def execute_function(func_id: int):
    start_time = time.time()
    success = False
    error_message = None
    backend_used = None

    try:
        runtime_backend = get_runtime_backend(func_id)
        backend_used = runtime_backend

        if runtime_backend not in ["docker", "gvisor"]:
            raise HTTPException(status_code=400, detail=f"Unsupported runtime backend: {runtime_backend}")

        # Get function info
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT code, language, timeout FROM functions WHERE id=?", (func_id,))
        row = cursor.fetchone()
        conn.close()

        if row is None:
            raise HTTPException(status_code=404, detail=f"Function with ID {func_id} not found")

        code, language, timeout = row
        image_name = SUPPORTED_LANGUAGES[language]["image_name"]

        # Use container pool (naively simulated by checking if image is marked warm)
        if container_pool.get(image_name, False):
            print(f"[Pool] Reusing warmed container for {language}...")
        else:
            print(f"[Pool] No warmed container. Warming now...")
            async_warm_up(language)

        # Execute function
        if runtime_backend == "docker":
            result = run_function_in_docker(func_id, code, language, timeout=timeout)
        elif runtime_backend == "gvisor":
            result = run_function_in_gvisor(language,code, timeout=timeout)

        success = True
        return {
            "status": "success",
            "data": result
        }

    except subprocess.TimeoutExpired:
        error_message = "Execution timed out"
        return {
            "status": "error",
            "error": error_message,
            "details": "The function execution exceeded the allowed time limit."
        }

    except Exception as e:
        error_message = str(e)
        traceback.print_exc()
        return {
            "status": "error",
            "error": "Internal server error",
            "details": error_message,
        }

    finally:
        duration = round(time.time() - start_time, 3)
        save_execution_metrics(func_id, success, duration, backend_used or "unknown", error_message)


@app.post("/functions/", response_model=Function)
def create_function(function_data: FunctionCreate):
    conn = get_db()
    cursor = conn.cursor()
    try:
        now = datetime.now()
        cursor.execute("""
            INSERT INTO functions (name, route, language, code, timeout, virtualization_backend, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            function_data.name,
            function_data.route,
            function_data.language,
            function_data.code,
            function_data.timeout,
            function_data.virtualization_backend,
            True,  # default is_active = True
            now,
            now
        ))
        conn.commit()
        func_id = cursor.lastrowid
        return Function(id=func_id, **function_data.dict(), is_active=True)
    except sqlite3.IntegrityError as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()

@app.get("/functions/", response_model=List[Function])
def list_functions():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, route, language, code, timeout, virtualization_backend, is_active FROM functions")
    rows = cursor.fetchall()
    conn.close()
    return [
        Function(
            id=row[0], name=row[1], route=row[2], language=row[3],
            code=row[4], timeout=row[5], virtualization_backend=row[6],
            is_active=bool(row[7])
        ) for row in rows
    ]

@app.get("/functions/{func_id}", response_model=Function)
def get_function(func_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, route, language, code, timeout, virtualization_backend, is_active FROM functions WHERE id=?", (func_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return Function(
            id=row[0], name=row[1], route=row[2], language=row[3],
            code=row[4], timeout=row[5], virtualization_backend=row[6],
            is_active=bool(row[7])
        )
    raise HTTPException(status_code=404, detail="Function not found")

@app.put("/functions/{func_id}", response_model=Function)
def update_function(func_id: int, function_data: FunctionCreate):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE functions
        SET name=?, route=?, language=?, code=?, timeout=?, virtualization_backend=?, updated_at=CURRENT_TIMESTAMP
        WHERE id=?
    """, (
        function_data.name,
        function_data.route,
        function_data.language,
        function_data.code,
        function_data.timeout,
        function_data.virtualization_backend,
        func_id
    ))
    conn.commit()
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Function not found")
    conn.close()
    return Function(id=func_id, **function_data.dict(), is_active=True)

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

# Optional test run for standalone execution
if __name__ == "__main__":
    print("Running sample Python function:")
    #result = run_function_in_docker("python", "print('Hello from Python!')", timeout=3)
    #print(result)
    async_warm_up("python")
    async_warm_up("javascript")

