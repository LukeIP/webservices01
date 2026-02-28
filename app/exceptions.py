"""Custom exception classes and global error handlers."""

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse


class AppException(Exception):
    """Base application exception."""
    def __init__(self, detail: str, status_code: int = 400, code: str = "APP_ERROR"):
        self.detail = detail
        self.status_code = status_code
        self.code = code


class NotFoundException(AppException):
    def __init__(self, resource: str, resource_id: int | str):
        super().__init__(
            detail=f"{resource} with id '{resource_id}' not found",
            status_code=404,
            code="NOT_FOUND",
        )


class DuplicateException(AppException):
    def __init__(self, resource: str, field: str, value: str):
        super().__init__(
            detail=f"{resource} with {field} '{value}' already exists",
            status_code=409,
            code="DUPLICATE",
        )


class ForbiddenException(AppException):
    def __init__(self, detail: str = "You do not have permission to perform this action"):
        super().__init__(detail=detail, status_code=403, code="FORBIDDEN")


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "code": exc.code},
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "code": "INTERNAL_ERROR"},
    )
