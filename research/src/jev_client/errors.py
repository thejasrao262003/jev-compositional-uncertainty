"""Exception types for the Jev API client.

Deliberately small: distinguishes transport-level failure (couldn't reach
the API) from HTTP-level failure (API responded with an error status) from
schema-level failure (API responded 200 but the body didn't match the
documented shape). Callers of JevClient.ask() do not need to catch these
directly for the characterization run — ask() catches them internally and
records the outcome in the returned record rather than raising, so one bad
call doesn't abort the run. They're raised only by lower-level helpers.
"""

from __future__ import annotations


class JevError(Exception):
    """Base class for all errors raised by this client."""


class JevConfigError(JevError):
    """Raised for missing/invalid client configuration (e.g. no API key)."""


class JevNetworkError(JevError):
    """Raised when the request could not complete (timeout, connection error)."""


class JevHTTPError(JevError):
    """Raised when the API returned a non-2xx HTTP status.

    Carries the status code and the response body (if any) so the caller
    can record it, but the body is not assumed to match any particular
    error schema - it's stored as-is.
    """

    def __init__(self, status_code: int, body: object):
        self.status_code = status_code
        self.body = body
        super().__init__(f"Jev API returned HTTP {status_code}")


class JevParseError(JevError):
    """Raised internally when a 200 response body doesn't match the
    documented schema. Not fatal to the run - ask() catches this and
    records parse_status='schema_mismatch' with the validation detail,
    while still preserving the raw response.
    """

    def __init__(self, detail: str):
        self.detail = detail
        super().__init__(detail)
