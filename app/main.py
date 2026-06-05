from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.database import Base, engine
from app.models import Archive, Like, Page, Report, Tag, User  # noqa: F401 — ensure models are registered
from app.models.restore_request import PageRestoreRequest  # noqa: F401
from app.routers import archives, auth, pages, users
from app.routers import likes, reports, tags

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Wiki API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(pages.router)
app.include_router(archives.router)
app.include_router(likes.router)
app.include_router(reports.router)
app.include_router(tags.router)

_static_dir = Path(__file__).parent.parent / "static"
app.mount("/static", StaticFiles(directory=_static_dir), name="static")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/")
def root():
    return FileResponse(_static_dir / "index.html")
