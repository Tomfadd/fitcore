from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from app.models.user import User
from app.schemas.schemas import RegisterRequest, LoginRequest, TokenResponse

router = APIRouter()

@router.post("/register", response_model=TokenResponse, status_code=201)
def register(payload: RegisterRequest, response: Response, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    conditions = list(payload.conditions)
    if payload.bmi > 30 and "obesity" not in conditions:
        conditions.append("obesity")
    user = User(name=payload.name, email=payload.email, password_hash=hash_password(payload.password),
                age=payload.age, gender=payload.gender, weight_kg=payload.weight_kg,
                height_cm=payload.height_cm, bmi=payload.bmi, rfm=payload.rfm,
                goal=payload.goal, conditions=conditions)
    db.add(user); db.commit(); db.refresh(user)
    _set_refresh_cookie(response, create_refresh_token({"sub": str(user.id)}))
    return {"access_token": create_access_token({"sub": str(user.id)}), "token_type": "bearer"}

@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    _set_refresh_cookie(response, create_refresh_token({"sub": str(user.id)}))
    return {"access_token": create_access_token({"sub": str(user.id)}), "token_type": "bearer"}

@router.post("/refresh", response_model=TokenResponse)
def refresh(response: Response, refresh_token: str = None, db: Session = Depends(get_db)):
    if not refresh_token: raise HTTPException(status_code=401, detail="Refresh token missing")
    payload = decode_token(refresh_token)
    if payload.get("type") != "refresh": raise HTTPException(status_code=401, detail="Invalid token type")
    user = db.query(User).filter(User.id == int(payload.get("sub"))).first()
    if not user: raise HTTPException(status_code=401, detail="User not found")
    return {"access_token": create_access_token({"sub": str(user.id)}), "token_type": "bearer"}

@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("refresh_token")
    return {"message": "Logged out"}

def _set_refresh_cookie(response, token):
    response.set_cookie(key="refresh_token", value=token, httponly=True, secure=True, samesite="lax", max_age=604800)
