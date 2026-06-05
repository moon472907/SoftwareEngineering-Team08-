from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.crud.archive import create_archive_v2_db
from app.models.page import Page
from app.schemas.page import PageCreate, PageUpdate


def _as_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """SQLite에서 읽어온 naive datetime을 UTC aware로 보정한다."""
    if dt is None:
        return None
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)


def lock_remaining_seconds(page: Page) -> Optional[int]:
    """락 만료까지 남은 시간(초). 잠겨 있지 않거나 만료됐으면 None."""
    if page.locked_by_id is None or page.locked_at is None:
        return None
    expires_at = _as_utc(page.locked_at) + timedelta(
        minutes=settings.EDIT_LOCK_TIMEOUT_MINUTES
    )
    remaining = (expires_at - datetime.now(timezone.utc)).total_seconds()
    return int(remaining) if remaining > 0 else None


def is_locked_by_other(page: Page, user_id: int) -> bool:
    """다른 사용자가 유효한(만료되지 않은) 락을 들고 있는지 여부."""
    if page.locked_by_id is None or page.locked_by_id == user_id:
        return False
    return lock_remaining_seconds(page) is not None


def acquire_lock(db: Session, page: Page, user_id: int) -> Page:
    """문서 락을 획득(또는 갱신)한다. 호출 전 is_locked_by_other로 확인할 것."""
    page.locked_by_id = user_id
    page.locked_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(page)
    return page


def release_lock(db: Session, page: Page) -> Page:
    """문서 락을 해제한다."""
    page.locked_by_id = None
    page.locked_at = None
    db.commit()
    db.refresh(page)
    return page


def get_page(db: Session, page_id: int) -> Optional[Page]:
    return db.query(Page).filter(Page.id == page_id, Page.is_deleted == False).first()


def get_page_by_title(db: Session, title: str) -> Optional[Page]:
    return db.query(Page).filter(Page.title == title, Page.is_deleted == False).first()


def get_pages(db: Session, skip: int = 0, limit: int = 20) -> list[Page]:
    return db.query(Page).filter(Page.is_deleted == False).offset(skip).limit(limit).all()


def create_page(db: Session, page_in: PageCreate, author_id: int) -> Page:
    page = Page(
        title=page_in.title,
        content=page_in.content,
        author_id=author_id,
    )
    db.add(page)
    db.commit()
    db.refresh(page)
    return page


def update_page(db: Session, page: Page, page_in: PageUpdate, editor_id: int) -> Page:
    # 수정 전 현재 버전을 아카이브에 저장 (Method 2: diff 기반). 편집 메모 함께 보관.
    create_archive_v2_db(db, page=page, editor_id=editor_id, memo=page_in.memo)

    if page_in.title is not None:
        page.title = page_in.title
    if page_in.content is not None:
        page.content = page_in.content

    page.last_editor_id = editor_id
    page.version += 1
    # 수정 완료 시 락 자동 해제
    page.locked_by_id = None
    page.locked_at = None
    db.commit()
    db.refresh(page)
    return page


def delete_page(db: Session, page: Page) -> Page:
    page.is_deleted = True
    db.commit()
    db.refresh(page)
    return page
