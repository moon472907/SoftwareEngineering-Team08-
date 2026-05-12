from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.database import Base, engine
from app.routers import archives, auth, pages, users

# 모델 인식 코드 
from app.models.restore_request import PageRestoreRequest 

# DB 테이블 자동 생성
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Wiki API")

app.add_middleware(
    CORSMiddleware,  #### cors 추가 
    allow_origins=["*"],  # 접속가능하게 
    allow_credentials=True,
    allow_methods=["*"],  # GET, POST 통과 
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(pages.router)
app.include_router(archives.router)

# 정적 파일 서빙 (/static/...)
_static_dir = Path(__file__).parent.parent / "static"
app.mount("/static", StaticFiles(directory=_static_dir), name="static")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/")
def root():
    return FileResponse(_static_dir / "index.html")