import threading

from scripts.load_test_autoscaling import ScaleEvent, monitor_scaling


class FakeECS:
    def __init__(self, counts: list[tuple[int, int]]) -> None:
        self.counts = counts
        self.calls = 0

    def describe_services(self, cluster: str, services: list[str]) -> dict:
        desired, running = self.counts[min(self.calls, len(self.counts) - 1)]
        self.calls += 1
        return {"services": [{"desiredCount": desired, "runningCount": running}]}


def test_monitor_scaling_stops_when_target_hit() -> None:
    ecs = FakeECS([(1, 1), (2, 1), (2, 2)])
    stop_event = threading.Event()
    log: list[ScaleEvent] = []

    result = monitor_scaling(ecs, "cluster", "service", target_count=2, poll_interval=0, timeout=5, stop_event=stop_event, log_events=log)

    assert result is not None
    assert result.running_count == 2
    assert stop_event.is_set()
    assert len(log) == 3


def test_monitor_scaling_times_out_without_hitting_target() -> None:
    ecs = FakeECS([(1, 1)])
    stop_event = threading.Event()
    log: list[ScaleEvent] = []

    result = monitor_scaling(ecs, "cluster", "service", target_count=2, poll_interval=0, timeout=0.05, stop_event=stop_event, log_events=log)

    assert result is None
    assert stop_event.is_set()
    assert len(log) > 0
