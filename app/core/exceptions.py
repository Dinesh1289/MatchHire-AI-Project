"""
Application-level exception hierarchy.

All domain exceptions inherit from AppError, which carries an HTTP status
code so the global exception handler can respond consistently.
"""

from http import HTTPStatus


class AppError(Exception):
    """Base for all application-level errors."""

    status_code: int = HTTPStatus.INTERNAL_SERVER_ERROR
    error_code: str = "INTERNAL_ERROR"

    def __init__(self, message: str, detail: str | None = None) -> None:
        self.message = message
        self.detail = detail
        super().__init__(message)


# ── File / Upload ──────────────────────────────────────────────────────────────


class FileTooLargeError(AppError):
    status_code = HTTPStatus.REQUEST_ENTITY_TOO_LARGE
    error_code = "FILE_TOO_LARGE"


class UnsupportedFileTypeError(AppError):
    status_code = HTTPStatus.UNPROCESSABLE_ENTITY
    error_code = "UNSUPPORTED_FILE_TYPE"


class CorruptedFileError(AppError):
    status_code = HTTPStatus.UNPROCESSABLE_ENTITY
    error_code = "CORRUPTED_FILE"


class EmptyFileError(AppError):
    status_code = HTTPStatus.UNPROCESSABLE_ENTITY
    error_code = "EMPTY_FILE"


# ── Parsing ────────────────────────────────────────────────────────────────────


class ParseError(AppError):
    status_code = HTTPStatus.UNPROCESSABLE_ENTITY
    error_code = "PARSE_ERROR"


class ExtractionError(AppError):
    status_code = HTTPStatus.UNPROCESSABLE_ENTITY
    error_code = "EXTRACTION_ERROR"


# ── Auth ───────────────────────────────────────────────────────────────────────


class AuthenticationError(AppError):
    status_code = HTTPStatus.UNAUTHORIZED
    error_code = "UNAUTHENTICATED"


class AuthorizationError(AppError):
    status_code = HTTPStatus.FORBIDDEN
    error_code = "FORBIDDEN"


# ── Resource ───────────────────────────────────────────────────────────────────


class NotFoundError(AppError):
    status_code = HTTPStatus.NOT_FOUND
    error_code = "NOT_FOUND"
