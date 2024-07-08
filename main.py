from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
import os
import threading
import time
from sqlite3 import Connection

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for testing purposes
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE = '/data/app.db'
db_lock = threading.Lock()

class Points(BaseModel):
    user_id: int
    points: int

class Register(BaseModel):
    user_id: int
    referral_code: str = ""

def get_db_connection() -> Connection:
    conn = sqlite3.connect(DATABASE, timeout=10, check_same_thread=False)  # Increase timeout and allow usage in multiple threads
    conn.row_factory = sqlite3.Row
    return conn

def execute_with_retry(conn: Connection, query: str, params=(), commit=False):
    max_retries = 10  # Increase max retries
    retry_delay = 2  # Increase delay between retries
    last_exception = None

    for _ in range(max_retries):
        try:
            cursor = conn.execute(query, params)
            if commit:
                conn.commit()
            return cursor
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e):
                last_exception = e
                time.sleep(retry_delay)
            else:
                raise
    raise HTTPException(status_code=500, detail=f"Database error after retries: {last_exception}")

@app.on_event("startup")
def startup():
    if not os.path.exists(DATABASE):
        with db_lock:
            conn = get_db_connection()
            with conn:
                conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    points INTEGER DEFAULT 0,
                    code TEXT
                )
                ''')
                conn.execute('''
                CREATE TABLE IF NOT EXISTS referrals (
                    user_id INTEGER,
                    referral_id INTEGER
                )
                ''')
            conn.close()

@app.get("/api/points")
def get_points(user_id: int):
    with db_lock:
        conn = get_db_connection()
        try:
            user = execute_with_retry(conn, "SELECT points FROM users WHERE user_id = ?", (user_id,)).fetchone()
            if user is None:
                raise HTTPException(status_code=404, detail="User not found")
            return {"points": user["points"]}
        finally:
            conn.close()

@app.post("/api/points/set")
def set_points(points: Points):
    with db_lock:
        conn = get_db_connection()
        try:
            execute_with_retry(conn, "UPDATE users SET points = ? WHERE user_id = ?", (points.points, points.user_id), commit=True)
            return {"status": "success"}
        except sqlite3.Error as e:
            raise HTTPException(status_code=500, detail=f"Database error: {e}")
        finally:
            conn.close()

@app.get("/api/link")
def get_link(user_id: int):
    with db_lock:
        conn = get_db_connection()
        try:
            user = execute_with_retry(conn, "SELECT code FROM users WHERE user_id = ?", (user_id,)).fetchone()
            if user is None:
                raise HTTPException(status_code=404, detail="User not found")
            return {"link": f"https://t.me/FHN_Telega_testWeb_bot/start?startapp={user['code']}"}
        finally:
            conn.close()

@app.get("/api/referralCount")
def get_referral_count(user_id: int):
    with db_lock:
        conn = get_db_connection()
        try:
            count = execute_with_retry(conn, "SELECT COUNT(*) as count FROM referrals WHERE referral_id = ?", (user_id,)).fetchone()
            return {"referral_count": count["count"]}
        finally:
            conn.close()

@app.post("/api/register")
def register_user(register: Register):
    with db_lock:
        conn = get_db_connection()
        try:
            code = f"ref{register.user_id}"
            execute_with_retry(conn, "INSERT INTO users (user_id, points, code) VALUES (?, 0, ?)", (register.user_id, code), commit=True)
            if register.referral_code:
                referral_user = execute_with_retry(conn, "SELECT user_id FROM users WHERE code = ?", (register.referral_code,)).fetchone()
                if referral_user:
                    execute_with_retry(conn, "INSERT INTO referrals (user_id, referral_id) VALUES (?, ?)", (register.user_id, referral_user["user_id"]), commit=True)
            return {"status": "success"}
        except sqlite3.IntegrityError as e:
            raise HTTPException(status_code=400, detail=f"User already exists: {e}")
        except sqlite3.Error as e:
            raise HTTPException(status_code=500, detail=f"Database error: {e}")
        finally:
            conn.close()

@app.options("/api/{path:path}")
async def options_handler(path: str):
    return {"status": "ok"}
