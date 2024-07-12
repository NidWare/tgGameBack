import os
import psycopg2
import threading
import time
from psycopg2.extras import RealDictCursor
from fastapi import HTTPException

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:password@db:5432/mydatabase')
db_lock = threading.Lock()

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

def create_tables():
    with db_lock:
        execute_with_retry('''
            CREATE TABLE IF NOT EXISTS users (
                user_id SERIAL PRIMARY KEY,
                points INTEGER DEFAULT 0,
                code TEXT,
                bonus_points INTEGER DEFAULT 0
            )
        ''', commit=True)
        execute_with_retry('''
            CREATE TABLE IF NOT EXISTS referrals (
                user_id INTEGER,
                referral_id INTEGER
            )
        ''', commit=True)
