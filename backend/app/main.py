import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings, setup_logging
from app.dependencies import AppException, app_exception_handler
from app.routers import documents, health, knowledge_bases

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    setup_logging()
    settings = get_settings()
    logger.info(
        "Starting Cite API | environment=%s", settings.environment
    )
    yield
    logger.info("Shutting down Cite API")


app = FastAPI(
    title="Weaverbit Cite API",
    description="AI-powered document Q&A platform with source citations",
    version="0.1.0",
    lifespan=lifespan,
)

settings = get_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.add_exception_handler(AppException, app_exception_handler)

app.include_router(health.router)
app.include_router(knowledge_bases.router)
app.include_router(documents.router)
