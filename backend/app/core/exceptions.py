import logging
import traceback
from typing import Any

from fastapi import Request
from fastapi import status as http_status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("novelverse")


def _setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format='{"time": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "msg": %(message)s}',
        datefmt="%Y-%m-%dT%H:%M:%S",
    )


def _sanitize_errors(errors: list[dict]) -> list[dict[str, Any]]:
    """Sanitize Pydantic v2 validation errors for JSON serialization.

    Pydantic v2 may include Exception objects in the ``ctx`` dict (e.g.
    ``{"error": ValueError(...)}``) which are not JSON-serializable.
    This converts them to their string representation.
    """
    sanitized = []
    for error in errors:
        err = dict(error)
        if "ctx" in err and isinstance(err["ctx"], dict):
            err["ctx"] = {
                k: str(v) if not isinstance(v, (str, int, float, bool, type(None))) else v
                for k, v in err["ctx"].items()
            }
        sanitized.append(err)
    return sanitized


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    logger.warning('{"status": %d, "path": "%s", "detail": "%s"}',
                   exc.status_code, request.url.path, exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=getattr(exc, "headers", None) or {},
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = _sanitize_errors(exc.errors())
    logger.info('{"status": 422, "path": "%s", "errors": %s}', request.url.path, errors)
    return JSONResponse(
        status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": errors},
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error('{"path": "%s", "error": "%s", "trace": "%s"}',
                 request.url.path,
                 str(exc),
                 traceback.format_exc().replace("\n", "\n"))
    return JSONResponse(
        status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )
