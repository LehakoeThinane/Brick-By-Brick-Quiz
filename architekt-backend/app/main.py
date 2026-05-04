from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.progress import router as progress_router
from app.api.questions import router as questions_router
from app.api.review_queue import router as review_queue_router
from app.api import auth, sessions, offline, analytics, content

app = FastAPI(title="ARCHITEKT API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, tags=["Authentication"])
app.include_router(sessions.router, tags=["Quiz Sessions"])
app.include_router(offline.router, prefix="/offline", tags=["Offline Sync"])
app.include_router(analytics.router, prefix="/analytics", tags=["Observability"])
app.include_router(content.router, prefix="/admin/content", tags=["AI Content Generation"])
app.include_router(questions_router)
app.include_router(progress_router)
app.include_router(review_queue_router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
