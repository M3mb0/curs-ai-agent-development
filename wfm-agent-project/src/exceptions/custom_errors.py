"""Defines custom exception types used across the project:
RateLimitError for signaling embedding API rate-limit issues, and
LLMUnavailableError / LLMConfigError for classifying failed LLM calls
as temporary or permanent.
"""


class RateLimitError(Exception):
    """Raised when an API call is rate-limited."""
    pass


class LLMUnavailableError(Exception):
    """Raised when an LLM call fails for a temporary reason (e.g. 429
    rate limit/quota, 503 server overloaded). Retrying later may work.
    """
    pass


class LLMConfigError(Exception):
    """Raised when an LLM call fails for a permanent reason (e.g. 404
    model not found, 400 bad request, 401/403 invalid API key or no
    permission). Retrying will not help until the configuration is fixed.
    """
    pass
