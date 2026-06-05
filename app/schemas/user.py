# schemas----- 회원가입 정보 조회 , 수정 , 로그인 etc..
from pydantic import BaseModel
from typing import Optional

# 회원가입 
class UserCreate(BaseModel):
    email: str
    password: str
    username : str

# 유저 정보 수정
class UserUpdate(BaseModel):
    username: Optional[str] = None

# 정보 조회 
class UserResponse(BaseModel):
    id: int
    email: str
    username: Optional[str] = None
    is_active: bool
    is_admin: bool

    model_config = {"from_attributes": True}

# 로그인 응답
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: Optional[str] = None

class UserReportCreate(BaseModel):
     reason: str  # 신고 사유