from fastapi import FastAPI

from app.config import get_settings

settings = get_settings()

app = FastAPI(title="Nimbus Agent Platform", version="0.1.0")


@app.get("/health")
def health_check() -> dict:
    """Basic liveness check used by Docker/CI and manual smoke tests."""
    return {"status": "ok", "env": settings.app_env}


# TODO(Phase 1): once app/api/routes.py has a chat router, wire it in here:
#     from app.api.routes import router as chat_router
#     app.include_router(chat_router, prefix="/api")
