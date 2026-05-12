from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from .user import User
    from .page import Page
    from .archive import Archive

class PageRestoreRequest(Base):
    __tablename__ = "page_restore_requests"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    page_id: Mapped[int] = mapped_column(ForeignKey("pages.id"), nullable=False)
    archive_id: Mapped[Optional[int]] = mapped_column(ForeignKey("archives.id"), nullable=True)
    requester_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    
    # 복원 이유 작성 
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    # 상태: 대기 , 승인, 거절 3단계 pending, approved, rejected
    status: Mapped[str] = mapped_column(String(50), default="PENDING")
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    page: Mapped["Page"] = relationship("Page")
    requester: Mapped["User"] = relationship("User")