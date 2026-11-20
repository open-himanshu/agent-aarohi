"""Worker supervisor recovery tests."""
from threading import Event

import pytest

from aarohi.worker_supervisor import WorkerSupervisor


class FlakyWorker:
    def __init__(self, failures):
        self.failures = failures
        self.calls = 0

    def run_forever(self, stop_event, *, poll_interval=1.0):
        self.calls += 1
        if self.failures:
            self.failures -= 1
            raise OSError("temporary storage failure")
        stop_event.set()
        return 2


def test_supervisor_restarts_after_infrastructure_failure():
    worker = FlakyWorker(2)
    delays = []
    supervisor = WorkerSupervisor(
        worker, max_restarts=3, base_delay_seconds=0.25,
        wait=lambda stop, seconds: delays.append(seconds) or False,
    )
    result = supervisor.run(Event())
    assert result == {"processed": 2, "restarts": 2}
    assert delays == [0.25, 0.5]
    assert worker.calls == 3


def test_supervisor_stops_after_restart_budget_exhausted():
    worker = FlakyWorker(10)
    supervisor = WorkerSupervisor(
        worker, max_restarts=1, wait=lambda stop, seconds: False,
    )
    with pytest.raises(OSError, match="temporary storage failure"):
        supervisor.run(Event())
    assert worker.calls == 2


def test_supervisor_validates_restart_policy():
    worker = FlakyWorker(0)
    with pytest.raises(ValueError, match="max_restarts"):
        WorkerSupervisor(worker, max_restarts=-1)
    with pytest.raises(ValueError, match="delays"):
        WorkerSupervisor(worker, base_delay_seconds=-1)
