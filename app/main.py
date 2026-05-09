from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.database import Base, engine
from app.models import Archive, Page, User  # noqa: F401 — ensure models are registered
from app.routers import auth, pages, users
from app.routers import archives

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Wiki API", version="1.0.0")

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(pages.router)
app.include_router(archives.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/")
def serve_index():
    return FileResponse("static/index.html")


app.mount("/static", StaticFiles(directory="static"), name="static")
