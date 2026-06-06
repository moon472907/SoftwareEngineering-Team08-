from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.crud.archive import create_archive_v2_db
from app.models.page import Page
from app.schemas.page import PageCreate, PageUpdate

TRASH_RETENTION_DAYS = 3


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
    # 수정 전 현재 버전을 아카이브에 저장 (Method 2: diff 기반)
    create_archive_v2_db(db, page=page, editor_id=editor_id)

    if page_in.title is not None:
        page.title = page_in.title
    if page_in.content is not None:
        page.content = page_in.content

    page.last_editor_id = editor_id
    page.version += 1
    db.commit()
    db.refresh(page)
    return page


def delete_page(db: Session, page: Page) -> Page:
    page.is_deleted = True
    page.deleted_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(page)
    return page


# ─── Trash ────────────────────────────────────

def purge_expired_pages(db: Session) -> None:
    """3일 이상 지난 소프트 삭제 페이지 영구 삭제"""
    cutoff = datetime.now(timezone.utc) - timedelta(days=TRASH_RETENTION_DAYS)
    expired = (
        db.query(Page)
        .filter(Page.is_deleted == True, Page.deleted_at <= cutoff)
        .all()
    )
    for page in expired:
        db.delete(page)
    if expired:
        db.commit()


def get_trash_pages(db: Session, user_id: int, is_admin: bool) -> list[Page]:
    """본인이 삭제한 페이지 목록 (관리자는 전체)"""
    purge_expired_pages(db)
    q = db.query(Page).filter(Page.is_deleted == True)
    if not is_admin:
        q = q.filter(Page.author_id == user_id)
    return q.order_by(Page.deleted_at.desc()).all()


def get_deleted_page(db: Session, page_id: int) -> Optional[Page]:
    return db.query(Page).filter(Page.id == page_id, Page.is_deleted == True).first()


def restore_page(db: Session, page: Page) -> Page:
    page.is_deleted = False
    page.deleted_at = None
    db.commit()
    db.refresh(page)
    return page


def permanent_delete_page(db: Session, page: Page) -> None:
    db.delete(page)
    db.commit()


def title_in_trash(db: Session, title: str) -> Optional[Page]:
    """삭제된 페이지 중 동일 제목 존재 여부"""
    purge_expired_pages(db)
    return db.query(Page).filter(Page.title == title, Page.is_deleted == True).first()
