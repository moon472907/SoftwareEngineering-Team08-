from sqlalchemy import create_engine, inspect, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# DB 파일 
SQLALCHEMY_DATABASE_URL = "sqlite:///./wiki.db"

# DB 연결 
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# 세션메이커 
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 기초 클래스 
Base = declarative_base()

# DB 함수
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_schema() -> None:
    """create_all 이 추가하지 못하는 신규 컬럼을 기존 테이블에 보강한다.

    SQLite의 ADD COLUMN을 이용한 경량 마이그레이션. 컬럼이 이미 있으면 건너뛰므로
    여러 번 호출해도 안전하다(idempotent). 기존 데이터는 보존된다.
    """
    # 추가할 컬럼: {테이블: [(컬럼명, 컬럼 정의), ...]}
    pending = {
        "pages": [
            ("locked_by_id", "INTEGER"),
            ("locked_at", "DATETIME"),
        ],
        "archives": [
            ("memo", "VARCHAR(500)"),
        ],
    }
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    with engine.begin() as conn:
        for table, columns in pending.items():
            if table not in existing_tables:
                continue
            existing_cols = {c["name"] for c in inspector.get_columns(table)}
            for name, ddl in columns:
                if name not in existing_cols:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}"))