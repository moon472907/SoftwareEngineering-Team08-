from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.crud.page import get_page
from app.crud.report import (
    create_report,
    get_all_reports,
    get_report,
    get_reports_by_page,
    has_reported,
    update_report_status,
)
from app.database import get_db
from app.dependencies import get_current_admin, get_current_user
from app.models.user import User
from app.schemas.report import ReportCreate, ReportListResponse, ReportResponse, ReportStatusUpdate

router = APIRouter(tags=["reports"])


@router.post("/pages/{page_id}/reports", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
def submit_report(
    page_id: int,
    report_in: ReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """페이지 신고 제출 (로그인 필요, 중복 신고 불가)"""
    if not get_page(db, page_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="페이지를 찾을 수 없습니다.")
    if has_reported(db, page_id=page_id, reporter_id=current_user.id):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="이미 신고한 페이지입니다.")
    return create_report(db, page_id=page_id, reporter_id=current_user.id, report_in=report_in)


@router.get("/pages/{page_id}/reports", response_model=list[ReportListResponse])
def list_page_reports(
    page_id: int,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """특정 페이지의 신고 목록 조회 (어드민 전용)"""
    if not get_page(db, page_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="페이지를 찾을 수 없습니다.")
    return get_reports_by_page(db, page_id=page_id, skip=skip, limit=limit)


@router.get("/reports", response_model=list[ReportListResponse])
def list_all_reports(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """전체 신고 목록 조회 (어드민 전용)"""
    return get_all_reports(db, skip=skip, limit=limit)


@router.patch("/reports/{report_id}", response_model=ReportResponse)
def update_report(
    report_id: int,
    update_in: ReportStatusUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """신고 처리 상태 변경 (어드민 전용): pending → reviewed → resolved"""
    report = get_report(db, report_id)
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="신고를 찾을 수 없습니다.")
    return update_report_status(db, report=report, update_in=update_in)
