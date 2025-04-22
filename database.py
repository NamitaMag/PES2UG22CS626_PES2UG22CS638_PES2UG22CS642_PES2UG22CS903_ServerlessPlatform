import sqlite3
from datetime import datetime

def init_db(db_path='lambda_platform.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('DROP TABLE IF EXISTS functions')

    # Create functions table
    cursor.execute('''
    CREATE TABLE functions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        route TEXT NOT NULL UNIQUE,
        language TEXT NOT NULL CHECK (language IN ('python', 'javascript')),
        code TEXT NOT NULL,
        timeout INTEGER DEFAULT 5,
        virtualization_backend TEXT CHECK (virtualization_backend IN ('docker', 'firecracker', 'nanos', 'gvisor')),
        is_active BOOLEAN DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Store metrics
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS execution_metrics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        function_id INTEGER,
        success BOOLEAN,
        duration REAL,
        backend_used TEXT,
        error_message TEXT,
        timestamp DATETIME,
        FOREIGN KEY(function_id) REFERENCES functions(id)
    )
    ''')




    # Create executions table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS executions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        function_id INTEGER NOT NULL,
        request_id TEXT NOT NULL UNIQUE,
        start_time DATETIME,
        end_time DATETIME,
        duration_ms INTEGER,
        status TEXT CHECK (status IN ('success', 'error', 'timeout')),
        response_code INTEGER,
        error_message TEXT,
        memory_used_mb REAL,
        cpu_time_ms REAL,
        FOREIGN KEY (function_id) REFERENCES functions(id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')              


    # Optional: function_stats table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS function_stats (
        function_id INTEGER PRIMARY KEY,
        total_requests INTEGER DEFAULT 0,
        avg_duration_ms REAL DEFAULT 0,
        success_rate REAL DEFAULT 0,
        last_invoked DATETIME,
        FOREIGN KEY (function_id) REFERENCES functions(id)
    )
    ''')

    conn.commit()
    conn.close()
    print("Database initialized successfully.")

DB_PATH = 'lambda_platform.db'

def get_runtime_backend(func_id: int) -> str:
    # Retrieve the runtime backend for a function by its ID from the DB.
    # For example, we assume 'docker' for now.
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT virtualization_backend FROM functions WHERE id=?", (func_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return row[0]  # This will return 'docker', 'gvisor', etc.
    else:
        return 'docker'  # Default backend

if __name__ == "__main__":
    init_db()

def save_execution_metrics(func_id: int, success: bool, duration: float, backend: str, error_msg: str = None):
    conn = sqlite3.connect('lambda_platform.db')
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO execution_metrics (function_id, success, duration, backend_used, error_message, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (func_id, int(success), duration, backend, error_msg, datetime.now()))
    conn.commit()
    conn.close()
