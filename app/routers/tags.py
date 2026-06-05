from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.crud.page import get_page
from app.crud.tag import add_tag_to_page, get_all_tags, get_pages_by_tag, remove_tag_from_page
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.page import PageListResponse
from app.schemas.tag import TagCreate, TagListResponse, TagResponse

router = APIRouter(tags=["tags"])


@router.get("/tags", response_model=TagListResponse)
def list_tags(db: Session = Depends(get_db)):
    """전체 태그 목록 조회 (누구나)"""
    tags = get_all_tags(db)
    return TagListResponse(tags=tags, total=len(tags))


@router.get("/tags/{tag_name}/pages", response_model=list[PageListResponse])
def list_pages_by_tag(
    tag_name: str,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """특정 태그가 달린 페이지 목록 조회 (누구나)"""
    return get_pages_by_tag(db, tag_name=tag_name, skip=skip, limit=limit)


@router.post("/pages/{page_id}/tags", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
def add_tag(
    page_id: int,
    tag_in: TagCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """페이지에 태그 추가 (로그인 필요)"""
    page = get_page(db, page_id)
    if not page:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="페이지를 찾을 수 없습니다.")
    return add_tag_to_page(db, page=page, tag_name=tag_in.name)


@router.delete("/pages/{page_id}/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_tag(
    page_id: int,
    tag_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """페이지에서 태그 제거 (로그인 필요)"""
    page = get_page(db, page_id)
    if not page:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="페이지를 찾을 수 없습니다.")
    if not remove_tag_from_page(db, page=page, tag_id=tag_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="해당 태그를 찾을 수 없습니다.")
