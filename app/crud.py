import math
from database import execute_with_retry

def get_points(user_id: int):
    result = execute_with_retry("SELECT points FROM users WHERE user_id = %s", (user_id,))
    if not result:
        return {"points": 0}
    return {"points": result[0]["points"]}

def set_points(points):
    execute_with_retry("UPDATE users SET points = %s WHERE user_id = %s", (points.points, points.user_id), commit=True)
    return {"status": "success"}

def add_points(points):
    execute_with_retry("UPDATE users SET points = points + %s WHERE user_id = %s", (points.points, points.user_id), commit=True)
    
    # Check if user was referred by someone
    referrer = execute_with_retry("SELECT referral_id FROM referrals WHERE user_id = %s", (points.user_id,))
    if referrer:
        referrer_id = referrer[0]['referral_id']
        bonus_points = math.ceil(points.points * 0.1)
        execute_with_retry("UPDATE users SET points = points + %s, bonus_points = bonus_points + %s WHERE user_id = %s", (bonus_points, bonus_points, referrer_id), commit=True)

    return {"status": "success"}

def get_link(user_id: int):
    result = execute_with_retry("SELECT code FROM users WHERE user_id = %s", (user_id,))
    if not result:
        raise HTTPException(status_code=404, detail="User not found")
    return {"link": f"https://t.me/FHN_Telega_testWeb_bot/start?startapp={result[0]['code']}"}

def get_referral_count(user_id: int):
    result = execute_with_retry("SELECT COUNT(*) as count FROM referrals WHERE referral_id = %s", (user_id,))
    return {"referral_count": result[0]["count"]}

def get_bonus_points(user_id: int):
    result = execute_with_retry("SELECT bonus_points FROM users WHERE user_id = %s", (user_id,))
    if not result:
        raise HTTPException(status_code=404, detail="User not found")
    return {"bonus_points": result[0]["bonus_points"]}

def register_user(register):
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
