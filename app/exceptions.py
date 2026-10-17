"""
Custom Exception Hierarchy for DBMS Operations and Input Validation.
Addresses ESE Rubric: Python Programming Implementation & Error Handling.
"""


class DBMSAppError(Exception):
    """Base exception class for all application-level errors."""

    def __init__(self, message: str, details: str = "", status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.details = details
        self.status_code = status_code


class DatabaseConnectionError(DBMSAppError):
    """Raised when SQL or NoSQL database connection fails and cannot recover."""

    def __init__(self, message: str, details: str = ""):
        super().__init__(message, details=details, status_code=500)


class QueryExecutionError(DBMSAppError):
    """Raised when an SQL query, stored procedure, or MongoDB pipeline fails."""

    def __init__(self, message: str, query_name: str = "", details: str = ""):
        super().__init__(message, details=details, status_code=500)
        self.query_name = query_name


class ValidationError(DBMSAppError):
    """Raised when user form input or API payload fails domain validation rules."""

    def __init__(self, message: str, field: str = "", details: str = ""):
        super().__init__(message, details=details, status_code=400)
        self.field = field
