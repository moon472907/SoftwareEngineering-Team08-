"""초기 데이터 시드.

서버가 처음 기동될 때 기본 관리자 계정이 없으면 생성한다.
여러 번 호출해도 안전하다(idempotent).
"""
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.database import SessionLocal
from app.models.user import User

# 기본 관리자 계정 정보
DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_EMAIL = "admin@admin.admin"
DEFAULT_ADMIN_PASSWORD = "Adminadmin"


def seed_admin(db: Session | None = None) -> None:
    """기본 관리자 계정이 없으면 1개 생성한다.

    계정 식별은 이메일을 기준으로 한다(임의 사용자명이 'admin'이라는 이유로
    관리자 권한이 부여되는 일을 막기 위함). 동일 이메일 계정이 이미 있으면
    관리자/활성 상태만 보장하고, 비밀번호 등 기존 값은 건드리지 않는다.
    """
    own_session = db is None
    if own_session:
        db = SessionLocal()
    try:
        admin = db.query(User).filter(User.email == DEFAULT_ADMIN_EMAIL).first()
        if admin:
            if not admin.is_admin or not admin.is_active:
                admin.is_admin = True
                admin.is_active = True
                db.commit()
            return

        # 이메일은 없지만 username 'admin' 이 이미 선점된 경우, 유니크 제약
        # 충돌을 피하기 위해 생성을 건너뛴다(기존 운영 데이터 보호).
        if db.query(User).filter(User.username == DEFAULT_ADMIN_USERNAME).first():
            return

        admin = User(
            username=DEFAULT_ADMIN_USERNAME,
            email=DEFAULT_ADMIN_EMAIL,
            hashed_password=hash_password(DEFAULT_ADMIN_PASSWORD),
            is_active=True,
            is_admin=True,
        )
        db.add(admin)
        db.commit()
    finally:
        if own_session:
            db.close()
