from sqlalchemy import create_engine
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