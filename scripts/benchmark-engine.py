#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import statistics
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "MyAgent-Engine"
if str(ENGINE) not in sys.path:
    sys.path.insert(0, str(ENGINE))


def run_worker(requests: int) -> None:
    import resource
    import tempfile
    import time
    import warnings

    warnings.filterwarnings("ignore", category=DeprecationWarning)
    started = time.perf_counter()
    from fastapi.testclient import TestClient

    from apps.backend.main import create_app
    from core.config.settings import Settings

    with tempfile.TemporaryDirectory() as directory:
        settings = Settings(
            ENVIRONMENT="testing",
            DEBUG=False,
            DATABASE_URL=f"sqlite+aiosqlite:///{Path(directory) / 'benchmark.db'}",
            AUTO_CREATE_TABLES=True,
            SEED_DEMO_USER=False,
            SECRET_KEY="benchmark-secret-key-with-more-than-32-characters",
            JWT_SECRET="benchmark-jwt-secret-with-more-than-32-characters",
            CORS_ORIGINS="http://localhost",
            TRUSTED_HOSTS="testserver",
            RATE_LIMIT_REQUESTS=max(1_000, requests * 2),
            DEFAULT_PROVIDER="mock",
        )
        application = create_app(settings)
        bootstrap_ms = (time.perf_counter() - started) * 1_000
        timings: list[float] = []
        with TestClient(application) as client:
            for _ in range(requests):
                request_started = time.perf_counter()
                response = client.get("/api/v1/health/live")
                response.raise_for_status()
                timings.append((time.perf_counter() - request_started) * 1_000)
        ordered = sorted(timings)
        p95_index = max(0, int(len(ordered) * 0.95) - 1)
        print(
            json.dumps(
                {
                    "bootstrap_ms": round(bootstrap_ms, 3),
                    "health_p50_ms": round(statistics.median(timings), 3),
                    "health_p95_ms": round(ordered[p95_index], 3),
                    "max_rss_kb": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                }
            )
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Reproducible MyAgent Engine benchmark")
    parser.add_argument("--samples", type=int, default=5)
    parser.add_argument("--requests", type=int, default=100)
    parser.add_argument("--worker", action="store_true")
    args = parser.parse_args()
    if args.samples < 1 or args.requests < 1:
        parser.error("samples and requests must be positive")
    if args.worker:
        run_worker(args.requests)
        return

    environment = {**os.environ, "LOG_LEVEL": "ERROR"}
    samples: list[dict[str, float]] = []
    for _ in range(args.samples):
        completed = subprocess.run(
            [
                sys.executable,
                __file__,
                "--worker",
                "--requests",
                str(args.requests),
            ],
            check=True,
            capture_output=True,
            text=True,
            env=environment,
        )
        samples.append(json.loads(completed.stdout.strip().splitlines()[-1]))
    medians = {
        key: round(statistics.median(sample[key] for sample in samples), 3) for key in samples[0]
    }
    print(json.dumps({"samples": samples, "median": medians}, indent=2))


if __name__ == "__main__":
    main()
