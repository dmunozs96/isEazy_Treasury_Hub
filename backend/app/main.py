from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import health, companies, imports, movements, classifications, intercompany, analytics

app = FastAPI(
    title="isEazy Treasury Hub API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api/v1")
app.include_router(companies.router, prefix="/api/v1")
app.include_router(imports.router, prefix="/api/v1")
app.include_router(movements.router, prefix="/api/v1")
app.include_router(classifications.router, prefix="/api/v1")
app.include_router(intercompany.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")
