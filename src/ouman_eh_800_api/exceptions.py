class OumanClientError(Exception):
    """Base exception for all Ouman client errors."""

    pass


class OumanClientAuthenticationError(OumanClientError):
    """Raised when authentication with the device fails."""

    pass


class OumanClientCommunicationError(OumanClientError):
    """Raised when communication with the device fails."""

    pass
