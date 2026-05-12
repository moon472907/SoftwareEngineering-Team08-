from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.crud.archive import get_archive, get_archives_by_page, reconstruct_content
from app.crud.page import get_page
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.archive import ArchiveListResponse, ArchiveResponse

router = APIRouter(prefix="/pages/{page_id}/archives", tags=["archives"])


@router.get("/", response_model=list[ArchiveListResponse])
def list_archives(
    page_id: int,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    if not get_page(db, page_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="페이지를 찾을 수 없습니다.")
    return get_archives_by_page(db, page_id=page_id, skip=skip, limit=limit)


@router.get("/{archive_id}", response_model=ArchiveResponse)
def read_archive(
    page_id: int,
    archive_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    archive = get_archive(db, archive_id)
    if not archive or archive.page_id != page_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="아카이브를 찾을 수 없습니다.")

    # diff 아카이브인 경우 전체 content 복원
    if archive.diff_data is not None:
        content = reconstruct_content(db, page_id, archive.version)
    else:
        content = archive.content or ""

    return ArchiveResponse(
        id=archive.id,
        page_id=archive.page_id,
        editor_id=archive.editor_id,
        title=archive.title,
        content=content,
        version=archive.version,
        archived_at=archive.archived_at,
    )
