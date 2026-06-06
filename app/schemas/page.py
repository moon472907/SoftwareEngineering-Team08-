from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.tag import TagResponse


class PageCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=1)


class PageUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    content: Optional[str] = Field(default=None, min_length=1)
    # 이번 수정에 대한 편집 메모(선택)
    memo: Optional[str] = Field(default=None, max_length=500)


class PageResponse(BaseModel):
    id: int
    title: str
    content: str
    author_id: int
    last_editor_id: Optional[int]
    version: int
    is_deleted: bool
    created_at: datetime
    updated_at: datetime
    locked_by_id: Optional[int] = None
    locked_at: Optional[datetime] = None
    tags: list[TagResponse] = []

    model_config = {"from_attributes": True}


class PageLockResponse(BaseModel):
    """락 상태 응답."""
    page_id: int
    locked: bool
    locked_by_id: Optional[int] = None
    locked_at: Optional[datetime] = None
    # 락 만료까지 남은 시간(초). 잠겨 있지 않으면 None.
    expires_in_seconds: Optional[int] = None


class PageListResponse(BaseModel):
    id: int
    title: str
    author_id: int
    version: int
    updated_at: datetime
    tags: list[TagResponse] = []

    model_config = {"from_attributes": True}


class TrashPageResponse(BaseModel):
    id: int
    title: str
    author_id: int
    deleted_at: Optional[datetime]

    model_config = {"from_attributes": True}
