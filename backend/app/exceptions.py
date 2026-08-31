class DomainException(Exception):
    """
    Base exception class for all domain-related errors.
    """
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class EntityNotFoundException(DomainException):
    """
    Exception thrown when a requested domain entity is not found.
    """
    pass


class BusinessRuleViolationException(DomainException):
    """
    Exception thrown when a business rule constraint is violated.
    """
    pass


class NoActiveWorkSessionError(BusinessRuleViolationException):
    """
    Exception thrown when an operation requires an active work session, but none exists.
    """
    pass


NoActiveWorkSessionException = NoActiveWorkSessionError

