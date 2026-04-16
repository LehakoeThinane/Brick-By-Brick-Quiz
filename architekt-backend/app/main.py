from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.api.progress import router as progress_router
from app.api.questions import router as questions_router
from app.api.review_queue import router as review_queue_router
from app.api.sessions import router as sessions_router

app = FastAPI(title="Architekt Backend")
app.include_router(auth_router)
app.include_router(questions_router)
app.include_router(sessions_router)
app.include_router(progress_router)
app.include_router(review_queue_router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
