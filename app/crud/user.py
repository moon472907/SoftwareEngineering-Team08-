from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import hash_password  
# get_password_hash에서 hash_password로 함수 이름 변경 

# 이메일로 유저 검색
def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

# 사용자명으로 유저 검색
def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

# ID로 유저 검색
def get_user_by_id(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

# 전체 유저 목록
def get_all_users(db: Session):
    return db.query(User).all()

# 회원가입
def create_user(db: Session, user: UserCreate):
    hashed_password = hash_password(user.password) 
    # get_password_hash에서 hash_password로 함수 이름 변경
    db_user = User(
        email=user.email,
        hashed_password=hashed_password, 
        username = user.username 
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# 유저 정보 수정
def update_user(db: Session, user: User, username: str):
    user.username = username
    db.commit()
    db.refresh(user)
    return user

# 계정 탈퇴 
def deactivate_user(db: Session, user: User):
    user.is_active = False
    db.commit()
    return user