"""Custom exceptions for the application"""


class AppError(Exception):
    """Base exception for all application errors"""

    def __init__(self, code: str, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class DuplicateEmailError(AppError):
    """User with this email already exists"""

    def __init__(self):
        super().__init__(
            "duplicate_email",
            "User with this email already exists",
            status_code=409,
        )


class InvalidCredentialsError(AppError):
    """Email or password is incorrect"""

    def __init__(self):
        super().__init__(
            "invalid_credentials",
            "Email or password is incorrect",
            status_code=401,
        )


class UserNotFoundError(AppError):
    """User not found"""

    def __init__(self):
        super().__init__(
            "user_not_found",
            "User not found",
            status_code=404,
        )


class ValidationError(AppError):
    """Validation error"""

    def __init__(self, message: str):
        super().__init__(
            "validation_error",
            message,
            status_code=400,
        )


class InvalidTokenError(AppError):
    """Invalid or expired token"""

    def __init__(self):
        super().__init__(
            "invalid_token",
            "Invalid or expired token",
            status_code=401,
        )
