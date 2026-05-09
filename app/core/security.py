from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
from app.core.config import settings

# 비밀번호 암호화 도구
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 1. 비밀번호를 암호로 바꾸기
def get_password_hash(password):
    return pwd_context.hash(password)

# 2. 비밀번호 확인
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# 3. 로그인 성공 시 JWT 토큰 발급 
def create_access_token(user_id: int):
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)