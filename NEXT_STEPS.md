# Next Steps to READY

The source candidate does not need architectural work. Execute the missing proof
on a clean connected runner.

## 1. GitHub Actions

Push the exact packaged source commit and run all jobs in `.github/workflows/ci.yml`:
`engine-sqlite`, `engine-postgres`, `clients`, `containers`, and `mobile`.
Do not reduce thresholds or make jobs optional.

## 2. Docker and Community Compose

```bash
docker build -t myagent-community-engine:3.0.0 .
docker build -t myagent-community-web:3.0.0 MyAgent-Web
docker compose config --quiet
docker compose up --build -d --wait --wait-timeout 180
./scripts/smoke-test.sh
docker compose down -v
```

Capture versions, image IDs, logs, health state, smoke output, and shutdown result.

## 3. Production PostgreSQL Compose

```bash
cp .env.production.example .env
# Replace every placeholder.
docker compose -f docker-compose.production.yml config --quiet
docker compose -f docker-compose.production.yml up --build -d --wait --wait-timeout 240
MYAGENT_API_URL=http://localhost:8080/api/v1 ./scripts/smoke-test.sh
docker compose -f docker-compose.production.yml restart engine
docker compose -f docker-compose.production.yml up -d --wait --wait-timeout 180
MYAGENT_API_URL=http://localhost:8080/api/v1 ./scripts/smoke-test.sh
```

Also run the refresh concurrency regression against PostgreSQL and verify data
persistence after restart.

## 4. Security and clients

Run `pip-audit --strict`, Electron Linux packaging, and Flutter format/analyze/test.
Any high or critical advisory blocks release unless a reviewed non-applicability
record is committed.

## 5. Render and Railway staging

Deploy each manifest separately. Verify migrations, readiness, registration,
login, refresh concurrency, chat, restart, persistence, HTTPS CORS, trusted hosts,
and rollback.

## 6. Close and package

Attach evidence to `RELEASE_CHECKLIST.md`, synchronize all audit/status files,
change status only when no mandatory box remains, then run:

```bash
make clean
make check
make package
sha256sum -c release/MyAgent-Community-Edition-v3.0.0.zip.sha256
```
