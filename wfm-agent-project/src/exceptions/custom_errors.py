"""Defines custom exception types used across the project, currently
RateLimitError for signaling API rate-limit issues.
"""


class RateLimitError(Exception):
    """Raised when an API call is rate-limited."""
    pass