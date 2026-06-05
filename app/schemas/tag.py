from pydantic import BaseModel, Field


class TagCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)


class TagResponse(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class TagListResponse(BaseModel):
    tags: list[TagResponse]
    total: int
