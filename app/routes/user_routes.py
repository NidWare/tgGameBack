from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models import Points, Register
import app.crud as crud
from app.database import get_db

router = APIRouter()

@router.get("/api/points")
def get_points(user_id: int, db: Session = Depends(get_db)):
    return crud.get_points(db, user_id)

@router.post("/api/points/set")
def set_points(points: Points, db: Session = Depends(get_db)):
    return crud.set_points(db, points)

@router.post("/api/points/add")
def add_points(points: Points, db: Session = Depends(get_db)):
    return crud.add_points(db, points)

@router.get("/api/link")
def get_link(user_id: int, db: Session = Depends(get_db)):
    return crud.get_link(db, user_id)

@router.get("/api/referralCount")
def get_referral_count(user_id: int, db: Session = Depends(get_db)):
    return crud.get_referral_count(db, user_id)

@router.get("/api/bonusPoints")
def get_bonus_points(user_id: int, db: Session = Depends(get_db)):
    return crud.get_bonus_points(user_id)

@router.post("/api/register")
def register_user(register: Register, db: Session = Depends(get_db)):
    return crud.register_user(db, register)

@router.options("/api/{path:path}")
async def options_handler(path: str):
    return {"status": "ok"}
