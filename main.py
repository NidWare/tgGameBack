from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import psycopg2
import os
import threading
import time
from psycopg2.extras import RealDictCursor

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for testing purposes
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:password@db:5432/mydatabase')
db_lock = threading.Lock()

class Points(BaseModel):
    user_id: int
    points: int

class Register(BaseModel):
    user_id: int
    referral_code: str = ""

def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL)
    return conn

def execute_with_retry(query, params=(), commit=False):
    max_retries = 10
    retry_delay = 2
    last_exception = None
    conn = get_db_connection()
    try:
        for _ in range(max_retries):
            try:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(query, params)
                    if commit:
                        conn.commit()
                    return cursor.fetchall() if not commit else None
            except psycopg2.OperationalError as e:
                last_exception = e
                time.sleep(retry_delay)
            except psycopg2.Error as e:
                raise HTTPException(status_code=500, detail=f"Database error: {e}")
        raise HTTPException(status_code=500, detail=f"Database error after retries: {last_exception}")
    finally:
        conn.close()

@app.on_event("startup")
def startup():
    with db_lock:
        execute_with_retry('''
            CREATE TABLE IF NOT EXISTS users (
                user_id SERIAL PRIMARY KEY,
                points INTEGER DEFAULT 0,
                code TEXT
            )
        ''', commit=True)
        execute_with_retry('''
            CREATE TABLE IF NOT EXISTS referrals (
                user_id INTEGER,
                referral_id INTEGER
            )
        ''', commit=True)

@app.get("/api/points")
def get_points(user_id: int):
    with db_lock:
        result = execute_with_retry("SELECT points FROM users WHERE user_id = %s", (user_id,))
        if not result:
            return {"points": 0}
        return {"points": result[0]["points"]}

@app.post("/api/points/set")
def set_points(points: Points):
    with db_lock:
        execute_with_retry("UPDATE users SET points = %s WHERE user_id = %s", (points.points, points.user_id), commit=True)
        return {"status": "success"}

@app.get("/api/link")
def get_link(user_id: int):
    with db_lock:
        result = execute_with_retry("SELECT code FROM users WHERE user_id = %s", (user_id,))
        if not result:
            raise HTTPException(status_code=404, detail="User not found")
        return {"link": f"https://t.me/FHN_Telega_testWeb_bot/start?startapp={result[0]['code']}"}

@app.get("/api/referralCount")
def get_referral_count(user_id: int):
    with db_lock:
        result = execute_with_retry("SELECT COUNT(*) as count FROM referrals WHERE referral_id = %s", (user_id,))
        return {"referral_count": result[0]["count"]}

@app.post("/api/register")
def register_user(register: Register):
    with db_lock:
        code = f"ref{register.user_id}"
        try:
            execute_with_retry("INSERT INTO users (user_id, points, code) VALUES (%s, 0, %s)", (register.user_id, code), commit=True)
            if register.referral_code:
                result = execute_with_retry("SELECT user_id FROM users WHERE code = %s", (register.referral_code,))
                if result:
                    referral_user = result[0]
                    execute_with_retry("INSERT INTO referrals (user_id, referral_id) VALUES (%s, %s)", (register.user_id, referral_user["user_id"]), commit=True)
                    # Add 200 points to the user who invited the newcomer
                    execute_with_retry("UPDATE users SET points = points + 200 WHERE user_id = %s", (referral_user["user_id"],), commit=True)
            return {"status": "success"}
        except psycopg2.IntegrityError as e:
            raise HTTPException(status_code=400, detail=f"User already exists: {e}")
        except psycopg2.Error as e:
            raise HTTPException(status_code=500, detail=f"Database error: {e}")

@app.options("/api/{path:path}")
async def options_handler(path: str):
    return {"status": "ok"}
