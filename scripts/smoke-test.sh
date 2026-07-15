#!/usr/bin/env sh
set -eu

base_url="${MYAGENT_API_URL:-http://localhost:8000/api/v1}"
email="${SMOKE_EMAIL:-smoke-$(date +%s)@example.com}"
password="${SMOKE_PASSWORD:-SmokeTest123!}"

python3 - "$base_url" "$email" "$password" <<'PY'
import json
import sys
import urllib.error
import urllib.request

base, email, password = sys.argv[1:]

def call(path, method="GET", body=None, token=None):
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(base + path, data=data, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read() or b"null")

health = call("/health/ready")
assert health["checks"]["database"] is True
try:
    tokens = call(
        "/auth/register",
        "POST",
        {"email": email, "password": password, "display_name": "Smoke Test"},
    )
except urllib.error.HTTPError as error:
    if error.code != 422:
        raise
    tokens = call("/auth/login", "POST", {"email": email, "password": password})
reply = call("/chat", "POST", {"message": "Community Edition smoke test"}, tokens["access_token"])
assert reply["conversation_id"].startswith("conv_")
assert reply["message"]
print("MYAGENT_SMOKE_TEST=PASS")
print(json.dumps({"health": health["status"], "provider": reply["provider"]}))
PY
