from typing import TYPE_CHECKING

from sqlalchemy.orm import Session

from app.models.archive import Archive

if TYPE_CHECKING:
    from app.models.page import Page


def get_archives_by_page(db: Session, page_id: int, skip: int = 0, limit: int = 20) -> list[Archive]:
    return (
        db.query(Archive)
        .filter(Archive.page_id == page_id)
        .order_by(Archive.version.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_archive(db: Session, archive_id: int) -> Archive | None:
    return db.query(Archive).filter(Archive.id == archive_id).first()


def create_archive(db: Session, page: "Page", editor_id: int) -> Archive:
    archive = Archive(
        page_id=page.id,
        editor_id=editor_id,
        title=page.title,
        content=page.content,
        version=page.version,
    )
    db.add(archive)
    db.flush()
    return archive
