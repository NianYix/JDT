"""Application errors and FastAPI exception handlers."""

import logging
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


class AppError(Exception):
    """Base application error with a stable client-facing code."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "app_error",
        status_code: int = 400,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code


def register_exception_handlers(app: FastAPI) -> None:
    """Attach unified JSON error responses to the FastAPI app."""

    @app.exception_handler(AppError)
    async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
        logger.warning("AppError [%s]: %s", exc.code, exc.message)
        body: dict[str, Any] = {"detail": exc.message, "code": exc.code}
        return JSONResponse(status_code=exc.status_code, content=body)

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
        # Do not swallow framework exceptions that already have handlers.
        if isinstance(exc, (HTTPException, StarletteHTTPException, RequestValidationError)):
            raise exc

        # SQLAdmin should surface real errors as HTML/text, not API JSON envelope.
        if request.url.path.startswith("/admin"):
            logger.exception("Unhandled admin exception on %s: %s", request.url.path, exc)
            from starlette.responses import PlainTextResponse

            return PlainTextResponse(
                content=f"{type(exc).__name__}: {exc}",
                status_code=500,
            )

        logger.exception("Unhandled exception on %s: %s", request.url.path, exc)
        body: dict[str, Any] = {
            "detail": "Internal server error",
            "code": "internal_error",
        }
        return JSONResponse(status_code=500, content=body)
