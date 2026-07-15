# MyAgent Web

Dependency-free static PWA for MyAgent Community Edition v3.0.

## Run

Serve this directory with any static server, or use the repository Compose file:

```bash
docker compose up --build web
```

The Nginx image proxies `/api/` and `/ws/` to the engine service. When serving the
files independently, configure the API base URL in the application UI.

## Development checks

```bash
node --check app.js
node --check sw.js
```

The service-worker cache namespace is versioned for v3. Do not cache authentication
responses or provider secrets.
