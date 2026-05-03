from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.crud.page import create_page, delete_page, get_page, get_page_by_title, get_pages, update_page
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.page import PageCreate, PageListResponse, PageResponse, PageUpdate

router = APIRouter(prefix="/pages", tags=["pages"])


@router.get("/", response_model=list[PageListResponse])
def list_pages(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    return get_pages(db, skip=skip, limit=limit)


@router.post("/", response_model=PageResponse, status_code=status.HTTP_201_CREATED)
def create(
    page_in: PageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if get_page_by_title(db, page_in.title):
        raise HTTPException(status_code=400, detail="동일한 제목의 페이지가 이미 존재합니다.")
    return create_page(db, page_in, author_id=current_user.id)


@router.get("/{page_id}", response_model=PageResponse)
def read_page(page_id: int, db: Session = Depends(get_db)):
    page = get_page(db, page_id)
    if not page:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="페이지를 찾을 수 없습니다.")
    return page


@router.put("/{page_id}", response_model=PageResponse)
def update(
    page_id: int,
    page_in: PageUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    page = get_page(db, page_id)
    if not page:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="페이지를 찾을 수 없습니다.")
    if page_in.title and page_in.title != page.title and get_page_by_title(db, page_in.title):
        raise HTTPException(status_code=400, detail="동일한 제목의 페이지가 이미 존재합니다.")
    return update_page(db, page, page_in, editor_id=current_user.id)


@router.delete("/{page_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(
    page_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    page = get_page(db, page_id)
    if not page:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="페이지를 찾을 수 없습니다.")
    # 작성자 또는 관리자만 삭제 가능
    if page.author_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="권한이 없습니다.")
    delete_page(db, page)
