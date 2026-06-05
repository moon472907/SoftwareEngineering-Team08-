from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.user import UserResponse, UserUpdate
from app.crud import user as user_crud
from app.dependencies import get_current_user, get_current_admin
from app.models.user import User
from app.models.user_report import UserReport # type: ignore
from app.schemas.user import UserReportCreate

router = APIRouter(prefix="/users", tags=["users"])

# 내 정보 조회
@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user

# 내 정보 수정
@router.put("/me", response_model=UserResponse)
def update_me(user_update: UserUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user_update.username:
        return user_crud.update_user(db, current_user, user_update.username)
    return current_user

# 전체 유저 목록 (관리자)
@router.get("/", response_model=list[UserResponse])
def get_all_users(db: Session = Depends(get_db), current_user: User = Depends(get_current_admin)):
    return user_crud.get_all_users(db)

# 특정 유저 조회
@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    user = user_crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="유저를 찾을 수 없습니다.")
    return user

# 계정 탈퇴 (본인, 관리자)
@router.delete("/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.id != user_id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="권한이 없습니다.")
    user = user_crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="유저를 찾을 수 없습니다.")
    return user_crud.deactivate_user(db, user)

# 유저 신고하기
@router.post("/{user_id}/report")
def report_user(
    user_id: int, 
    report_data: UserReportCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1.  신고 대상
    reported_user = user_crud.get_user_by_id(db, user_id)
    if not reported_user:
        raise HTTPException(status_code=404, detail="신고할 유저를 찾을 수 없습니다.")
    
    # 2. 신고 내역 DB에 저장
    new_report = UserReport(
        reported_id=user_id,             # URL에서 받은 신고 당할 사람 ID
        reporter_id=current_user.id,     # JWT 토큰에서 꺼낸 내(신고자) ID
        reason=report_data.reason        # 프론트엔드에서 보낸 신고 사유
    )
    
    db.add(new_report)
    db.commit()
    db.refresh(new_report)
    
    return {"message": "신고가 성공적으로 접수되었습니다.", "report_id": new_report.id}