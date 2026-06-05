from typing import Optional

from sqlalchemy.orm import Session

from app.models.page import Page
from app.models.tag import Tag


def get_tag_by_name(db: Session, name: str) -> Optional[Tag]:
    return db.query(Tag).filter(Tag.name == name).first()


def get_tag_by_id(db: Session, tag_id: int) -> Optional[Tag]:
    return db.query(Tag).filter(Tag.id == tag_id).first()


def get_all_tags(db: Session) -> list[Tag]:
    return db.query(Tag).order_by(Tag.name).all()


def get_or_create_tag(db: Session, name: str) -> Tag:
    """태그가 없으면 생성, 있으면 기존 태그 반환."""
    name = name.strip().lower()
    tag = get_tag_by_name(db, name)
    if not tag:
        tag = Tag(name=name)
        db.add(tag)
        db.flush()
    return tag


def add_tag_to_page(db: Session, page: Page, tag_name: str) -> Tag:
    tag = get_or_create_tag(db, tag_name)
    if tag not in page.tags:
        page.tags.append(tag)
        db.commit()
    return tag


def remove_tag_from_page(db: Session, page: Page, tag_id: int) -> bool:
    tag = get_tag_by_id(db, tag_id)
    if not tag or tag not in page.tags:
        return False
    page.tags.remove(tag)
    db.commit()
    return True


def get_pages_by_tag(db: Session, tag_name: str, skip: int = 0, limit: int = 20) -> list[Page]:
    tag_name = tag_name.strip().lower()
    return (
        db.query(Page)
        .join(Page.tags)
        .filter(Tag.name == tag_name, Page.is_deleted == False)
        .offset(skip)
        .limit(limit)
        .all()
    )
