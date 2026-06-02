from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ReportCreate(BaseModel):
    reason: str = Field(min_length=5, max_length=500)


class ReportStatusUpdate(BaseModel):
    status: str = Field(pattern="^(pending|reviewed|resolved)$")
    admin_note: Optional[str] = Field(default=None, max_length=500)


class ReportResponse(BaseModel):
    id: int
    page_id: int
    reporter_id: int
    reason: str
    status: str
    admin_note: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ReportListResponse(BaseModel):
    id: int
    page_id: int
    reporter_id: int
    reason: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
