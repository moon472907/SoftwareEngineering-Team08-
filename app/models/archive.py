from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from .user import User
    from .page import Page


class Archive(Base):
    __tablename__ = "archives"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    page_id: Mapped[int] = mapped_column(ForeignKey("pages.id"), nullable=False, index=True)
    editor_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    # Method 1: 전체 내용 저장 (base 아카이브 또는 레거시)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Method 2: Myers diff 결과(JSON) 저장 — content가 None일 때 사용
    diff_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    archived_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    page: Mapped["Page"] = relationship("Page", back_populates="archives")
    editor: Mapped["User"] = relationship("User", back_populates="archives")
