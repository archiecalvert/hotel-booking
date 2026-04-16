"""
exceptions
~~~~~~~~~~
This module contains exceptions that are thrown by the ReservationApi
when the API responds with a non-200 or 5xx error
"""

from requests.exceptions import RequestException

# 400 error
class BadRequestError(RequestException):
    """A 400 Bad Request error occurred."""
    def __init__(self):
        self.code = 400
        super().__init__("A 400 Bad Request error occurred.")

# 401 error
class InvalidTokenError(RequestException):
    """The API token was invalid or missing."""
    def __init__(self):
        self.code = 401
        super().__init__("The API token was invalid or missing.")

# 403 error
class BadSlotError(RequestException):
    """The requested slot does not exist."""
    def __init__(self):
        self.code = 403
        super().__init__("The requested slot does not exist.")

# 404 error
class NotProcessedError(RequestException):
    """The request has not been processed."""
    def __init__(self):
        self.code = 404
        super().__init__("The request has not been processed.")

# 409 error
class SlotUnavailableError(RequestException):
    """The requested slot is not available."""
    def __init__(self):
        self.code = 409
        super().__init__("The requested slot is not available.")

# 451 error
class ReservationLimitError(RequestException):
    """The client already holds the maximum number of reservations."""
    def __init__(self):
        self.code = 451
        super().__init__("The client already holds the maximum number of reservations.")
