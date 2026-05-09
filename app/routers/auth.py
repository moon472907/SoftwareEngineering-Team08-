from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.user import UserCreate, UserResponse
from app.crud import user as user_crud
from app.core.security import verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])

# 회원가입
@router.post("/register", response_model=UserResponse)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    db_user = user_crud.get_user_by_email(db, email=user_data.email)
    if db_user:
        raise HTTPException(status_code=400, detail="이미 가입된 이메일입니다. ")
    return user_crud.create_user(db=db, user=user_data)

# 로그인
@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = user_crud.get_user_by_email(db, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 존재하지 않습니다.")
    token = create_access_token(user.id)
    return {"access_token": token, "token_type": "bearer"}