#!/usr/bin/env python3
"""Load test the Fargate service and watch it autoscale via boto3.

Hammers /burn concurrently until the ECS service's running task count
reaches --target-count (or --timeout), polling desired/running counts
along the way and writing them to --output as JSON lines.

Example:
    python scripts/load_test_autoscaling.py \\
        --url https://xxxx.execute-api.us-east-1.amazonaws.com
"""
from __future__ import annotations

import argparse
import json
import sys
import threading
import time
from dataclasses import asdict, dataclass


@dataclass
class ScaleEvent:
    timestamp: float
    desired_count: int
    running_count: int


def monitor_scaling(
    ecs_client,
    cluster: str,
    service: str,
    target_count: int,
    poll_interval: float,
    timeout: float,
    stop_event: threading.Event,
    log_events: list[ScaleEvent],
) -> ScaleEvent | None:
    """Poll ECS service counts until target_count is reached or timeout elapses.

    Returns the ScaleEvent that first hit target_count, or None on timeout.
    Sets stop_event either way, so load-generating workers know to stop.
    """
    deadline = time.monotonic() + timeout
    result = None
    while time.monotonic() < deadline:
        resp = ecs_client.describe_services(cluster=cluster, services=[service])
        svc = resp["services"][0]
        event = ScaleEvent(time.time(), svc["desiredCount"], svc["runningCount"])
        log_events.append(event)
        print(f"[monitor] desired={event.desired_count} running={event.running_count}")
        if event.running_count >= target_count:
            result = event
            break
        if stop_event.wait(poll_interval):
            break
    stop_event.set()
    return result


def burn_worker(url: str, burn_seconds: float, stop_event: threading.Event, counters: dict) -> None:
    import httpx

    with httpx.Client(timeout=burn_seconds + 10) as client:
        while not stop_event.is_set():
            try:
                r = client.get(f"{url}/burn", params={"seconds": burn_seconds})
                counters["ok" if r.status_code == 200 else "error"] += 1
            except httpx.HTTPError:
                counters["error"] += 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--url", required=True, help="API base URL")
    parser.add_argument("--cluster", default="aws-fargate-demo")
    parser.add_argument("--service", default="app")
    parser.add_argument("--region", default="us-east-1")
    parser.add_argument("--target-count", type=int, default=2)
    parser.add_argument("--workers", type=int, default=20)
    parser.add_argument("--burn-seconds", type=float, default=3.0)
    parser.add_argument("--poll-interval", type=float, default=15.0)
    parser.add_argument("--timeout", type=float, default=900.0, help="Give up after this many seconds")
    parser.add_argument("--output", default="load_test_results.jsonl")
    args = parser.parse_args()

    import boto3

    stop_event = threading.Event()
    counters = {"ok": 0, "error": 0}
    log_events: list[ScaleEvent] = []

    ecs = boto3.client("ecs", region_name=args.region)

    workers = [
        threading.Thread(target=burn_worker, args=(args.url, args.burn_seconds, stop_event, counters), daemon=True)
        for _ in range(args.workers)
    ]
    for w in workers:
        w.start()

    hit = monitor_scaling(
        ecs, args.cluster, args.service, args.target_count,
        args.poll_interval, args.timeout, stop_event, log_events,
    )

    for w in workers:
        w.join(timeout=5)

    with open(args.output, "w") as f:
        for event in log_events:
            f.write(json.dumps(asdict(event)) + "\n")

    print(f"requests: ok={counters['ok']} error={counters['error']}")
    print(f"wrote {len(log_events)} scale samples to {args.output}")

    if hit is None:
        print(f"TIMEOUT: never reached running_count>={args.target_count}")
        return 1
    print(f"SCALED: running_count={hit.running_count} at {time.ctime(hit.timestamp)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
