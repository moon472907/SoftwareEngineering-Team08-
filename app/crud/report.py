from typing import Optional

from sqlalchemy.orm import Session

from app.models.report import Report
from app.schemas.report import ReportCreate, ReportStatusUpdate


def create_report(db: Session, page_id: int, reporter_id: int, report_in: ReportCreate) -> Report:
    report = Report(
        page_id=page_id,
        reporter_id=reporter_id,
        reason=report_in.reason,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


def get_report(db: Session, report_id: int) -> Optional[Report]:
    return db.query(Report).filter(Report.id == report_id).first()


def get_reports_by_page(db: Session, page_id: int, skip: int = 0, limit: int = 20) -> list[Report]:
    return (
        db.query(Report)
        .filter(Report.page_id == page_id)
        .order_by(Report.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_all_reports(db: Session, skip: int = 0, limit: int = 20) -> list[Report]:
    return (
        db.query(Report)
        .order_by(Report.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def has_reported(db: Session, page_id: int, reporter_id: int) -> bool:
    return (
        db.query(Report)
        .filter(Report.page_id == page_id, Report.reporter_id == reporter_id)
        .first()
        is not None
    )


def update_report_status(db: Session, report: Report, update_in: ReportStatusUpdate) -> Report:
    report.status = update_in.status
    if update_in.admin_note is not None:
        report.admin_note = update_in.admin_note
    db.commit()
    db.refresh(report)
    return report
