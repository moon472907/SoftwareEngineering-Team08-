from datetime import datetime

from pydantic import BaseModel


class LikeStatus(BaseModel):
    page_id: int
    like_count: int
    is_liked: bool

    model_config = {"from_attributes": True}


class LikedUserItem(BaseModel):
    user_id: int
    username: str
    liked_at: datetime

    model_config = {"from_attributes": True}


class LikedUsersResponse(BaseModel):
    page_id: int
    like_count: int
    users: list[LikedUserItem]
