from fastapi import FastAPI
from app.database import engine, Base
from app.routers import auth, users, pages # main.py에 pages 추가 

# DB 테이블 자동 생성
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Wiki API")

# 라우터 등록
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(pages.router)  # 페이지 화면 추가  

@app.get("/health")
def health():
    return {"status": "ok"}