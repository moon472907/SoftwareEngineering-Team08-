from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.crud.like import get_like_count, get_liked_users, has_liked, toggle_like
from app.crud.page import get_page
from app.database import get_db
from app.dependencies import get_current_admin, get_current_user, get_optional_current_user
from app.models.user import User
from app.schemas.like import LikeStatus, LikedUsersResponse

router = APIRouter(prefix="/pages", tags=["likes"])


@router.get("/{page_id}/likes", response_model=LikeStatus)
def get_page_likes(
    page_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    """좋아요 수 조회. 로그인 시 본인의 좋아요 여부도 포함."""
    page = get_page(db, page_id)
    if not page:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="페이지를 찾을 수 없습니다.")
    like_count = get_like_count(db, page_id)
    is_liked = has_liked(db, current_user.id, page_id) if current_user else False
    return LikeStatus(page_id=page_id, like_count=like_count, is_liked=is_liked)


@router.post("/{page_id}/likes", response_model=LikeStatus)
def toggle_page_like(
    page_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """좋아요 토글 (로그인 필요). 이미 눌렀으면 취소, 아니면 좋아요."""
    page = get_page(db, page_id)
    if not page:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="페이지를 찾을 수 없습니다.")
    is_liked = toggle_like(db, user_id=current_user.id, page_id=page_id)
    like_count = get_like_count(db, page_id)
    return LikeStatus(page_id=page_id, like_count=like_count, is_liked=is_liked)


@router.get("/{page_id}/likes/users", response_model=LikedUsersResponse)
def get_page_liked_users(
    page_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """좋아요 누른 유저 목록 조회 (관리자 전용)."""
    page = get_page(db, page_id)
    if not page:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="페이지를 찾을 수 없습니다.")
    users = get_liked_users(db, page_id)
    return LikedUsersResponse(page_id=page_id, like_count=len(users), users=users)
