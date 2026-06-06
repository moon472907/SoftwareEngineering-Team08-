from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ArchiveResponse(BaseModel):
    id: int
    page_id: int
    editor_id: int
    title: str
    content: str
    version: int
    memo: Optional[str] = None
    archived_at: datetime

    model_config = {"from_attributes": True}


class ArchiveListResponse(BaseModel):
    id: int
    page_id: int
    editor_id: int
    title: str
    version: int
    memo: Optional[str] = None
    archived_at: datetime

    model_config = {"from_attributes": True}
