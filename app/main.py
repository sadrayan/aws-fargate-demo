import time

from fastapi import FastAPI

app = FastAPI(title="aws-fargate-demo")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/hello")
def hello() -> dict[str, str]:
    return {"message": "Hello from Fargate demo"}


@app.get("/burn")
def burn(seconds: float = 2.0) -> dict[str, float]:
    """Pegs one CPU core for `seconds` (clamped 0.1-10) — for autoscaling load tests."""
    seconds = max(0.1, min(seconds, 10.0))
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        pass
    return {"burned_seconds": seconds}
