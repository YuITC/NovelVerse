from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.core.exceptions import (
    _setup_logging,
    http_exception_handler,
    validation_exception_handler,
    unhandled_exception_handler,
)
from app.core.rate_limit import rate_limit
from app.api.v1.router import api_router

_setup_logging()

app = FastAPI(
    title="NovelVerse API",
    version="0.1.0",
    docs_url=f"{settings.api_prefix}/docs",
    openapi_url=f"{settings.api_prefix}/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register exception handlers
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

# Include API router with global rate limiting dependency
app.include_router(
    api_router,
    prefix=settings.api_prefix,
    dependencies=[Depends(rate_limit)],
)
