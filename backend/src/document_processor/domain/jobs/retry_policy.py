from __future__ import annotations

from datetime import UTC, datetime, timedelta

# Delay in seconds after each failed attempt: 30s, 2m, 8m, 32m, 2h
RETRY_DELAYS_SECONDS: list[int] = [30, 120, 480, 1920, 7200]


def compute_next_retry_at(attempt_number: int) -> datetime | None:
    """
    Returns the datetime for the next retry after a failed attempt.
    Returns None when all retry slots are exhausted → caller should set dead_letter.

    attempt_number is 1-based (the number of the attempt that just failed).
    """
    idx = attempt_number - 1
    if idx >= len(RETRY_DELAYS_SECONDS):
        return None
    delay = RETRY_DELAYS_SECONDS[idx]
    return datetime.now(UTC) + timedelta(seconds=delay)


def should_dead_letter(attempt_number: int, max_attempts: int) -> bool:
    """Returns True when the job has exhausted all allowed attempts."""
    return attempt_number >= max_attempts
