from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from .user import User
    from .archive import Archive
    from .tag import Tag


class Page(Base):
    __tablename__ = "pages"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    last_editor_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    version: Mapped[int] = mapped_column(default=1)
    is_deleted: Mapped[bool] = mapped_column(default=False)
    # 동시 수정 방지용 락. 락을 잡은 사용자와 잡은 시각을 기록한다.
    # locked_by_id 가 None 이면 잠겨 있지 않은 상태.
    locked_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    locked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    author: Mapped["User"] = relationship("User", back_populates="pages", foreign_keys=[author_id])
    last_editor: Mapped[Optional["User"]] = relationship("User", foreign_keys=[last_editor_id])
    locked_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[locked_by_id])
    archives: Mapped[list["Archive"]] = relationship("Archive", back_populates="page")
    tags: Mapped[list["Tag"]] = relationship("Tag", secondary="page_tags", backref="pages")
