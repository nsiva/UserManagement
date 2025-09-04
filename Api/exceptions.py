"""
Custom exception classes for user-friendly error handling.
"""

class UserManagementError(Exception):
    """Base exception for user management operations."""
    def __init__(self, message: str, user_message: str = None, error_code: str = None):
        self.message = message
        self.user_message = user_message or message
        self.error_code = error_code
        super().__init__(self.message)

class DuplicateEmailError(UserManagementError):
    """Raised when attempting to create a user with an existing email."""
    def __init__(self, email: str):
        message = f"User with email '{email}' already exists"
        user_message = "A user with this email address already exists. Please use a different email or check if the user is already registered."
        super().__init__(message, user_message, "DUPLICATE_EMAIL")

class ConstraintViolationError(UserManagementError):
    """Raised when a database constraint is violated."""
    def __init__(self, constraint_name: str, details: str = None):
        message = f"Database constraint violation: {constraint_name}"
        if details:
            message += f" - {details}"
        
        # Map common constraints to user-friendly messages
        constraint_messages = {
            "aaa_profiles_email_key": "This email address is already registered. Please use a different email.",
            "aaa_profiles_pkey": "A user with this ID already exists.",
            "not_null": "All required fields must be filled in.",
            "check_constraint": "The provided data does not meet the required format."
        }
        
        user_message = constraint_messages.get(constraint_name, "The provided information is invalid. Please check your input and try again.")
        super().__init__(message, user_message, "CONSTRAINT_VIOLATION")

class UserNotFoundError(UserManagementError):
    """Raised when a requested user is not found."""
    def __init__(self, identifier: str):
        message = f"User not found: {identifier}"
        user_message = "The requested user could not be found."
        super().__init__(message, user_message, "USER_NOT_FOUND")

class DatabaseConnectionError(UserManagementError):
    """Raised when database connection fails."""
    def __init__(self, details: str = None):
        message = f"Database connection error: {details}" if details else "Database connection error"
        user_message = "Service is temporarily unavailable. Please try again in a few moments."
        super().__init__(message, user_message, "DATABASE_CONNECTION_ERROR")

class InvalidDataError(UserManagementError):
    """Raised when provided data is invalid."""
    def __init__(self, field: str, reason: str = None):
        message = f"Invalid data for field '{field}'"
        if reason:
            message += f": {reason}"
        
        user_message = f"The {field} field contains invalid data. Please check and try again."
        super().__init__(message, user_message, "INVALID_DATA")

class AuthorizationError(UserManagementError):
    """Raised when user lacks permission for an operation."""
    def __init__(self, operation: str):
        message = f"Insufficient permissions for operation: {operation}"
        user_message = "You don't have permission to perform this action."
        super().__init__(message, user_message, "AUTHORIZATION_ERROR")