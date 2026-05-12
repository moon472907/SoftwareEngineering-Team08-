from typing import Optional

from sqlalchemy.orm import Session

from app.crud.archive import create_archive_v2_db
from app.models.page import Page
from app.schemas.page import PageCreate, PageUpdate


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
    db.commit()
    db.refresh(page)
    return page
