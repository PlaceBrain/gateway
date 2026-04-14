from typing import Annotated, Any

from fastapi import Depends, Query
from pydantic import BaseModel


class PaginatedResponse[T](BaseModel):
    items: list[T]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool


class ErrorResponse(BaseModel):
    detail: str


class SuccessResponse(BaseModel):
    success: bool


class DeleteResponse(BaseModel):
    success: bool
    warnings: list[str] = []


class _PaginationParams:
    def __init__(
        self,
        page: int = Query(1, ge=1, description="Page number"),
        per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    ):
        self.page = page
        self.per_page = per_page


PaginationParams = Annotated[_PaginationParams, Depends()]


# Shared error response dicts for OpenAPI documentation
AUTH_ERRORS: dict[int | str, dict[str, Any]] = {
    401: {"description": "Not authenticated", "model": ErrorResponse}
}
FORBIDDEN_ERRORS: dict[int | str, dict[str, Any]] = {
    403: {"description": "Permission denied", "model": ErrorResponse}
}
NOT_FOUND_ERRORS: dict[int | str, dict[str, Any]] = {
    404: {"description": "Resource not found", "model": ErrorResponse}
}
CONFLICT_ERRORS: dict[int | str, dict[str, Any]] = {
    409: {"description": "Resource already exists", "model": ErrorResponse}
}
