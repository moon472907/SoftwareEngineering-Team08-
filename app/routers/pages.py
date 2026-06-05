from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.crud.page import (
    acquire_lock,
    create_page,
    delete_page,
    get_page,
    get_page_by_title,
    get_pages,
    is_locked_by_other,
    lock_remaining_seconds,
    release_lock,
    update_page,
)
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.page import (
    PageCreate,
    PageListResponse,
    PageLockResponse,
    PageResponse,
    PageUpdate,
)

####### 복원 모델 
from app.models.restore_request import PageRestoreRequest
from app.models.page import Page
from app.models.archive import Archive

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
    if is_locked_by_other(page, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=f"다른 사용자가 수정 중인 문서입니다. (locked_by_id={page.locked_by_id})",
        )
    if page_in.title and page_in.title != page.title and get_page_by_title(db, page_in.title):
        raise HTTPException(status_code=400, detail="동일한 제목의 페이지가 이미 존재합니다.")
    # update_page 내부에서 저장 후 락을 자동 해제한다.
    return update_page(db, page, page_in, editor_id=current_user.id)


@router.post("/{page_id}/lock", response_model=PageLockResponse, summary="수정 락 획득")
def lock_page(
    page_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """수정을 시작할 때 문서 락을 잡는다.

    - 다른 사용자가 유효한 락을 들고 있으면 423 Locked.
    - 본인이 이미 잡았거나 락이 만료된 경우 새로 획득(갱신)한다.
    """
    page = get_page(db, page_id)
    if not page:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="페이지를 찾을 수 없습니다.")
    if is_locked_by_other(page, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=f"다른 사용자가 수정 중인 문서입니다. (locked_by_id={page.locked_by_id})",
        )
    acquire_lock(db, page, current_user.id)
    return PageLockResponse(
        page_id=page.id,
        locked=True,
        locked_by_id=page.locked_by_id,
        locked_at=page.locked_at,
        expires_in_seconds=lock_remaining_seconds(page),
    )


@router.delete("/{page_id}/lock", response_model=PageLockResponse, summary="수정 락 해제")
def unlock_page(
    page_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """수정을 취소/완료할 때 락을 푼다. 락 소유자 또는 관리자만 해제할 수 있다."""
    page = get_page(db, page_id)
    if not page:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="페이지를 찾을 수 없습니다.")
    if (
        page.locked_by_id is not None
        and page.locked_by_id != current_user.id
        and not current_user.is_admin
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="락을 소유한 사용자 또는 관리자만 해제할 수 있습니다.",
        )
    release_lock(db, page)
    return PageLockResponse(page_id=page.id, locked=False)


@router.get("/{page_id}/lock", response_model=PageLockResponse, summary="수정 락 상태 조회")
def get_lock_status(page_id: int, db: Session = Depends(get_db)):
    """문서의 현재 락 상태를 조회한다."""
    page = get_page(db, page_id)
    if not page:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="페이지를 찾을 수 없습니다.")
    remaining = lock_remaining_seconds(page)
    locked = remaining is not None
    return PageLockResponse(
        page_id=page.id,
        locked=locked,
        locked_by_id=page.locked_by_id if locked else None,
        locked_at=page.locked_at if locked else None,
        expires_in_seconds=remaining,
    )


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

@router.post("/{page_id}/restore-request", summary="restore reaquest")
def request_page_restore(
    page_id: int, 
    reason: str, 
    archive_id: int = None, 
    db: Session = Depends(get_db)
):
    page = db.query(Page).filter(Page.id == page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="페이지를 찾을 수 없습니다.")

    existing_request = db.query(PageRestoreRequest).filter(
        PageRestoreRequest.page_id == page_id,
        PageRestoreRequest.status == "PENDING"
    ).first()
    
    if existing_request:
        raise HTTPException(status_code=400, detail="이미 복원 요청이 접수된 문서입니다.")

    new_request = PageRestoreRequest(
        page_id=page_id,
        archive_id=archive_id,
        requester_id=1, # (나중에 current_user.id 로 변경 필요)
        reason=reason
    )
    db.add(new_request)
    db.commit()

    return {"message": "문서 복원 요청이 접수되었습니다."}


@router.put("/restore-requests/{request_id}/approve", summary="restore requests approve")
def approve_page_restore(
    request_id: int, 
    db: Session = Depends(get_db)
):
    req = db.query(PageRestoreRequest).filter(PageRestoreRequest.id == request_id).first()
    if not req or req.status != "PENDING":
        raise HTTPException(status_code=400, detail="유효하지 않거나 이미 처리된 요청입니다.")

    page = db.query(Page).filter(Page.id == req.page_id).first()

    # 과거 버전으로 
    if req.archive_id:
        archive = db.query(Archive).filter(Archive.id == req.archive_id).first()
        if archive:
            page.content = archive.content 
            page.title = archive.title

    req.status = "APPROVED"
    db.commit()
    
    return {"message": "복원 요청이 승인되어 문서가 원상 복구되었습니다."}
