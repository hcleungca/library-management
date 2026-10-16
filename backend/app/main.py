from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.books import router as books_router
from app.api.circulation import router as circulation_router
from app.api.health import router as health_router
from app.api.search import router as search_router
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(health_router, prefix=settings.API_V1_STR)
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(search_router, prefix=settings.API_V1_STR)
app.include_router(books_router, prefix=settings.API_V1_STR)
app.include_router(circulation_router, prefix=settings.API_V1_STR)


@app.get("/")
def root() -> dict[str, str]:
    """Root health and welcome endpoint."""
    return {"message": "Intelligent Library API is running"}
