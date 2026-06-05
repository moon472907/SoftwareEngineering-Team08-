from sqlalchemy import Column, ForeignKey, Integer, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

# 중간 연결 테이블 (Page ↔ Tag 다대다)
page_tags = Table(
    "page_tags",
    Base.metadata,
    Column("page_id", Integer, ForeignKey("pages.id"), primary_key=True),
    Column("tag_id",  Integer, ForeignKey("tags.id"),  primary_key=True),
)


class Tag(Base):
    __tablename__ = "tags"

    id:   Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
