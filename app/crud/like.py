from sqlalchemy.orm import Session

from app.models.like import Like
from app.models.user import User
from app.schemas.like import LikedUserItem


def get_like_count(db: Session, page_id: int) -> int:
    return db.query(Like).filter(Like.page_id == page_id).count()


def has_liked(db: Session, user_id: int, page_id: int) -> bool:
    return (
        db.query(Like).filter(Like.user_id == user_id, Like.page_id == page_id).first()
        is not None
    )


def toggle_like(db: Session, user_id: int, page_id: int) -> bool:
    """좋아요 토글. 좋아요 상태이면 True, 취소 상태이면 False 반환."""
    existing = db.query(Like).filter(Like.user_id == user_id, Like.page_id == page_id).first()
    if existing:
        db.delete(existing)
        db.commit()
        return False
    db.add(Like(user_id=user_id, page_id=page_id))
    db.commit()
    return True


def get_liked_users(db: Session, page_id: int) -> list[LikedUserItem]:
    likes = db.query(Like).filter(Like.page_id == page_id).all()
    result = []
    for like in likes:
        user = db.query(User).filter(User.id == like.user_id).first()
        if user:
            result.append(
                LikedUserItem(user_id=user.id, username=user.username, liked_at=like.created_at)
            )
    return result
