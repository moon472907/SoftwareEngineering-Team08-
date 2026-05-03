from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class PageCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=1)


class PageUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    content: Optional[str] = Field(default=None, min_length=1)


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

    model_config = {"from_attributes": True}


class PageListResponse(BaseModel):
    id: int
    title: str
    author_id: int
    version: int
    updated_at: datetime

    model_config = {"from_attributes": True}
