"""Domain exceptions - Business rule violations."""


class DomainError(Exception):
    """Base exception for all domain errors."""

    pass


class InvalidStateError(DomainError):
    """Raised when an operation is invalid for the current state.

    Example: Trying to complete a run that hasn't started yet.
    """

    pass


class NotFoundError(DomainError):
    """Raised when a requested entity is not found.

    Example: Trying to get a run that doesn't exist.
    """

    def __init__(self, entity_type: str, entity_id: str):
        self.entity_type = entity_type
        self.entity_id = entity_id
        super().__init__(f"{entity_type} not found: {entity_id}")


class AlreadyExistsError(DomainError):
    """Raised when trying to create an entity that already exists.

    Example: Trying to create a run with an ID that's already in use.
    """

    def __init__(self, entity_type: str, entity_id: str):
        self.entity_type = entity_type
        self.entity_id = entity_id
        super().__init__(f"{entity_type} already exists: {entity_id}")


class ValidationError(DomainError):
    """Raised when entity data fails validation.

    Example: Creating a run with an empty goal.
    """

    pass


class PermissionDeniedError(DomainError):
    """Raised when an operation is not permitted.

    Example: Trying to modify a file outside the project scope.
    """

    pass
