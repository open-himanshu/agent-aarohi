"""Bounded in-process restart supervisor for a trusted Aarohi worker."""
from __future__ import annotations

from collections.abc import Callable
from threading import Event

from aarohi.queue import Worker


class WorkerSupervisor:
    """Restart a worker loop after infrastructure errors, with bounded backoff."""

    def __init__(
        self, worker: Worker, *, max_restarts: int = 3,
        base_delay_seconds: float = 1.0, max_delay_seconds: float = 30.0,
        wait: Callable[[Event, float], bool] | None = None,
    ):
        if max_restarts < 0:
            raise ValueError("max_restarts cannot be negative")
        if base_delay_seconds < 0 or max_delay_seconds < 0:
            raise ValueError("restart delays cannot be negative")
        self.worker = worker
        self.max_restarts = max_restarts
        self.base_delay_seconds = base_delay_seconds
        self.max_delay_seconds = max_delay_seconds
        self.wait = wait or (lambda stop, seconds: stop.wait(seconds))

    def run(self, stop_event: Event, *, poll_interval: float = 1.0) -> dict[str, int]:
        """Run until stopped or restart budget is exhausted; handler errors are queue-managed."""
        restarts = 0
        processed = 0
        while not stop_event.is_set():
            try:
                processed += self.worker.run_forever(
                    stop_event, poll_interval=poll_interval,
                )
                break
            except Exception:
                if stop_event.is_set() or restarts >= self.max_restarts:
                    raise
                delay = min(
                    self.base_delay_seconds * (2 ** restarts),
                    self.max_delay_seconds,
                )
                restarts += 1
                if self.wait(stop_event, delay):
                    break
        return {"processed": processed, "restarts": restarts}
