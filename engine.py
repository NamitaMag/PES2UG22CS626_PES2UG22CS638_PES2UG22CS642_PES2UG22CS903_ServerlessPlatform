import os
import shutil
import subprocess
import uuid
import time
from pathlib import Path
import sqlite3
import threading
from fastapi import HTTPException

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

# Global container pool (image_name -> bool indicating warm state)
container_pool = {}

DB_PATH = 'lambda_platform.db'
FUNCTIONS_DIR = Path("functions")
FUNCTIONS_DIR.mkdir(exist_ok=True)
#CONTAINER_POOL = {}

# --- Utility: Metrics Store ---
METRICS = []

def store_metric(func_id, backend, start_time, end_time, error=None):
    METRICS.append({
        "func_id": func_id,
        "backend": backend,
        "response_time": end_time - start_time,
        "error": error,
        "timestamp": time.time()
    })

# --- Function Execution Engine ---
def run_function(func_id: int, code: str, language: str, timeout: int = 5, backend: str = "docker") -> dict:
    start_time = time.time()
    try:
        if backend == "docker":
            result = run_function_in_docker(func_id, code, language, timeout)
        elif backend == "gvisor":
            result = run_function_in_gvisor(language, code, timeout)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported backend: {backend}")
        end_time = time.time()
        store_metric(func_id, backend, start_time, end_time, error=result.get("error"))
        return result
    except Exception as e:
        end_time = time.time()
        store_metric(func_id, backend, start_time, end_time, error=str(e))
        raise HTTPException(status_code=500, detail=f"Execution error: {e}")

def run_function_in_docker(func_id: int, code: str, language: str, timeout: int = 5) -> dict:
    temp_dir = Path("temp") / uuid.uuid4().hex
    temp_dir.mkdir(parents=True, exist_ok=True)

    try:
        config = SUPPORTED_LANGUAGES[language]
        code_filename = config["filename"]
        original_dockerfile = config["dockerfile"]
        dockerfile_path = temp_dir / "Dockerfile"
        shutil.copy(original_dockerfile, dockerfile_path)

        image_name = config["image_name"]

        with open(temp_dir / code_filename, "w") as f:
            f.write(code)

        # Check if a container already exists for this image
        if image_name in container_pool:
            container_name = container_pool[image_name]
            print(f"[Pool] Reusing warmed container for {language}...")

            result = subprocess.run(
                ["docker", "start", "-a", container_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout
            )
            return {
                "stdout": result.stdout.decode(),
                "stderr": result.stderr.decode(),
                "timeout": False
            }

        # Build image and warm a container if not in pool
        subprocess.run(
            ["docker", "build", "-t", image_name, "-f", str(dockerfile_path.name), "."],
            cwd=temp_dir,
            check=True
        )

        container_name = f"{image_name}-warm-{uuid.uuid4().hex[:6]}"
        container_pool[image_name] = container_name

        subprocess.run(
            ["docker", "run", "-dit", "--name", container_name, image_name],
            check=True
        )

        result = subprocess.run(
            ["docker", "start", "-a", container_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout
        )

        return {
            "stdout": result.stdout.decode(),
            "stderr": result.stderr.decode(),
            "timeout": False
        }

    except subprocess.TimeoutExpired:
        return {"error": "Execution timed out", "timeout": True}
    except subprocess.CalledProcessError as e:
        return {"error": f"Docker error: {e}", "timeout": False}
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def run_function_in_gvisor(language: str, code: str, timeout: int = 5) -> dict:
    if language not in SUPPORTED_LANGUAGES:
        return {"error": f"Unsupported language: {language}"}

    config = SUPPORTED_LANGUAGES[language]
    code_filename = config["filename"]
    dockerfile_name = config["dockerfile"]
    image_name = config["image_name"]

    # Reuse warmed container if available
    if image_name in container_pool:
        container_name = container_pool[image_name]
        print(f"[Pool] Reusing warmed container for {language}...")

        try:
            result = subprocess.run(
                ["docker", "start", "-a", container_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout
            )
            return {
                "stdout": result.stdout.decode(),
                "stderr": result.stderr.decode(),
                "timeout": False
            }

        except subprocess.TimeoutExpired:
            return {"error": "Execution timed out", "timeout": True}
        except subprocess.CalledProcessError as e:
            return {"error": f"gVisor error (reuse): {e}", "timeout": False}

    # Otherwise, build and warm a new container
    container_name = f"{image_name}-warm-{uuid.uuid4().hex[:6]}"
    container_pool[image_name] = container_name

    temp_dir = FUNCTIONS_DIR / uuid.uuid4().hex
    temp_dir.mkdir(parents=True, exist_ok=True)

    try:
        code_path = temp_dir / code_filename
        with open(code_path, "w") as f:
            f.write(code)

        # Copy correct Dockerfile to temp_dir/Dockerfile
        shutil.copy(dockerfile_name, temp_dir / "Dockerfile")

        subprocess.run(
            [
                "docker", "buildx", "build",
                "--platform", "linux/amd64",
                "-t", image_name,
                "-f", "Dockerfile",
                "."
            ],
            cwd=temp_dir,
            check=True
        )

        # Start container in detached mode to warm it
        subprocess.run(
            [
                "docker", "run",
                "-dit",
                "--runtime=gvisor",
                "--name", container_name,
                image_name
            ],
            check=True
        )

        # Attach and execute
        result = subprocess.run(
            ["docker", "start", "-a", container_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout
        )

        return {
            "stdout": result.stdout.decode(),
            "stderr": result.stderr.decode(),
            "timeout": False
        }

    except subprocess.TimeoutExpired:
        return {"error": "Execution timed out", "timeout": True}
    except subprocess.CalledProcessError as e:
        return {"error": f"gVisor error: {e}", "timeout": False}
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


# --- Metrics API (Optional Utility Functions) ---
def get_all_metrics():
    return METRICS

def get_metrics_for_func(func_id: int):
    return [m for m in METRICS if m["func_id"] == func_id]
