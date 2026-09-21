"""Minimal, documented Jev API client for characterization (Step 0A).

Scope, deliberately: make one call, record everything about it, never
crash the run on a single bad/unexpected response, never expose the API
key. This is NOT the full Phase-2 client described in the original project
spec (no persistent structured-logging framework, no cost-tracking
dashboard) - it is sized for a ~20-call characterization run. Extend it
later if Step 0A's findings justify a larger run.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import requests
from pydantic import ValidationError

from .errors import JevConfigError, JevHTTPError, JevNetworkError
from .schemas import JevResponseBody

logger = logging.getLogger("jev_client")

DEFAULT_BASE_URL = "https://api.typesafe.ai/v1/systemone"
DEFAULT_MODEL = "jev-latest"
DEFAULT_TIMEOUT_S = 30.0
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
MAX_RETRIES = 2
BACKOFF_BASE_S = 1.0


def _sha256(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _load_api_key() -> str:
    """Loads JEV_API_KEY from the environment (via a .env file if present).

    Never logs or returns the key in any form other than the raw string
    handed to the caller for building the Authorization header. Callers
    of this module must not print/log the return value.
    """
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass
    key = os.environ.get("JEV_API_KEY")
    if not key:
        raise JevConfigError(
            "JEV_API_KEY not found in environment or .env file. "
            "Set it before running the characterization client."
        )
    return key


@dataclass
class ClientConfig:
    base_url: str = DEFAULT_BASE_URL
    model: str = DEFAULT_MODEL
    timeout_s: float = DEFAULT_TIMEOUT_S
    max_retries: int = MAX_RETRIES

    def redacted_dict(self) -> dict[str, Any]:
        """Config fields that are safe to persist to run_metadata.json -
        excludes the API key by construction (it's never stored here)."""
        return {
            "base_url": self.base_url,
            "model": self.model,
            "timeout_s": self.timeout_s,
            "max_retries": self.max_retries,
        }

    def config_hash(self) -> str:
        return _sha256(json.dumps(self.redacted_dict(), sort_keys=True))


@dataclass
class CallRecord:
    """One row of the characterization dataset. Field names match the
    conceptual schema requested for the run - see
    research/methodology/... for the rationale. `raw_response` is the
    unmodified JSON body (or None on total transport failure); it is the
    source of truth if anything here disagrees with `parsed_response`.
    """

    request_id: str
    timestamp_utc: str
    test_group: str
    primitives: list[str]
    state: str
    questions_spec: dict[str, Any]
    request_parameters: dict[str, Any]
    input_hash: str
    config_hash: str
    is_retry: bool
    attempt: int
    http_status: int | None
    latency_ms: float
    raw_response: Any
    parsed_response: dict[str, Any] | None
    parse_status: str  # "success" | "schema_mismatch" | "http_error" | "network_error"
    parse_notes: list[str] = field(default_factory=list)
    error: dict[str, str] | None = None

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "timestamp_utc": self.timestamp_utc,
            "test_group": self.test_group,
            "primitives": self.primitives,
            "state": self.state,
            "questions_spec": self.questions_spec,
            "request_parameters": self.request_parameters,
            "input_hash": self.input_hash,
            "config_hash": self.config_hash,
            "is_retry": self.is_retry,
            "attempt": self.attempt,
            "http_status": self.http_status,
            "latency_ms": self.latency_ms,
            "raw_response": self.raw_response,
            "parsed_response": self.parsed_response,
            "parse_status": self.parse_status,
            "parse_notes": self.parse_notes,
            "error": self.error,
        }


class JevClient:
    def __init__(self, config: ClientConfig | None = None, api_key: str | None = None):
        self.config = config or ClientConfig()
        self._api_key = api_key or _load_api_key()

    def _headers(self) -> dict[str, str]:
        # Never logged. Constructed fresh per call so nothing holds a
        # long-lived reference to a string containing the header value.
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

    def ask(
        self,
        *,
        state: str,
        questions: dict[str, dict[str, Any]],
        test_group: str,
    ) -> CallRecord:
        """Sends one request (possibly with multiple mixed questions) and
        returns a fully-populated CallRecord. Never raises for HTTP-level
        or schema-level problems - those are recorded, not thrown, so a
        single unexpected response doesn't abort the characterization run.
        Only a client-configuration error (missing key) raises, and that
        happens in __init__, not here.
        """
        request_id = str(uuid.uuid4())
        body = {"state": state, "model": self.config.model, "questions": questions}
        input_hash = _sha256(json.dumps({"state": state, "questions": questions}, sort_keys=True))
        primitives = [q.get("type", "?") for q in questions.values()]

        attempt = 0
        is_retry = False
        last_exc: Exception | None = None

        while attempt <= self.config.max_retries:
            attempt += 1
            start = time.perf_counter()
            try:
                resp = requests.post(
                    self.config.base_url,
                    headers=self._headers(),
                    json=body,
                    timeout=self.config.timeout_s,
                )
                latency_ms = (time.perf_counter() - start) * 1000
            except requests.exceptions.RequestException as exc:
                latency_ms = (time.perf_counter() - start) * 1000
                last_exc = exc
                # Network-level failure - retry if attempts remain.
                if attempt <= self.config.max_retries:
                    is_retry = True
                    time.sleep(BACKOFF_BASE_S * attempt)
                    continue
                return self._record(
                    request_id, test_group, primitives, state, questions, body,
                    input_hash, is_retry, attempt, http_status=None,
                    latency_ms=latency_ms, raw_response=None,
                    parse_status="network_error",
                    error={"type": type(exc).__name__, "message": str(exc)[:500]},
                )

            # Got an HTTP response - decide whether it's retryable.
            if resp.status_code in RETRYABLE_STATUS_CODES and attempt <= self.config.max_retries:
                is_retry = True
                time.sleep(BACKOFF_BASE_S * attempt)
                continue

            try:
                raw = resp.json()
            except ValueError:
                raw = {"_non_json_body": resp.text[:2000]}

            if resp.status_code != 200:
                return self._record(
                    request_id, test_group, primitives, state, questions, body,
                    input_hash, is_retry, attempt, http_status=resp.status_code,
                    latency_ms=latency_ms, raw_response=raw,
                    parse_status="http_error",
                    error={"type": "JevHTTPError", "message": f"HTTP {resp.status_code}"},
                )

            parsed_dict: dict[str, Any] | None = None
            parse_status = "success"
            parse_notes: list[str] = []
            try:
                parsed = JevResponseBody.model_validate(raw)
                parsed_dict = parsed.model_dump()
                extra = getattr(parsed, "model_extra", None)
                if extra:
                    parse_notes.append(f"undocumented top-level fields present: {sorted(extra.keys())}")
                for key, ans in parsed.answers.items():
                    ans_extra = getattr(ans, "model_extra", None)
                    if ans_extra:
                        parse_notes.append(f"answer '{key}': undocumented fields present: {sorted(ans_extra.keys())}")
            except ValidationError as exc:
                parse_status = "schema_mismatch"
                parse_notes.append(str(exc))

            rec = self._record(
                request_id, test_group, primitives, state, questions, body,
                input_hash, is_retry, attempt, http_status=resp.status_code,
                latency_ms=latency_ms, raw_response=raw,
                parse_status=parse_status, parsed_response=parsed_dict,
                parse_notes=parse_notes,
            )
            return rec

        # Exhausted retries on a network error without returning above
        # (defensive; loop above always returns before falling through).
        raise JevNetworkError(str(last_exc))

    def _record(
        self, request_id, test_group, primitives, state, questions, body,
        input_hash, is_retry, attempt, *, http_status, latency_ms, raw_response,
        parse_status, parsed_response=None, parse_notes=None, error=None,
    ) -> CallRecord:
        return CallRecord(
            request_id=request_id,
            timestamp_utc=datetime.now(timezone.utc).isoformat(),
            test_group=test_group,
            primitives=primitives,
            state=state,
            questions_spec=questions,
            request_parameters={"model": self.config.model, "timeout_s": self.config.timeout_s},
            input_hash=input_hash,
            config_hash=self.config.config_hash(),
            is_retry=is_retry,
            attempt=attempt,
            http_status=http_status,
            latency_ms=round(latency_ms, 2),
            raw_response=raw_response,
            parsed_response=parsed_response,
            parse_status=parse_status,
            parse_notes=parse_notes or [],
            error=error,
        )
