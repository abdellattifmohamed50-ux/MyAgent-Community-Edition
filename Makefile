PYTHON ?= python3
ENGINE_DIR := MyAgent-Engine
VENV := $(ENGINE_DIR)/.venv
PY := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

.PHONY: setup migrate run test coverage format lint typecheck security openapi check \
        compose-config start stop logs smoke benchmark package clean

setup:
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -e "$(ENGINE_DIR)[dev]"

migrate:
	cd $(ENGINE_DIR) && .venv/bin/alembic upgrade head

run: migrate
	cd $(ENGINE_DIR) && .venv/bin/uvicorn apps.backend.main:app --reload --host 127.0.0.1 --port 8000

test:
	cd $(ENGINE_DIR) && .venv/bin/pytest -q

coverage:
	cd $(ENGINE_DIR) && .venv/bin/pytest -q --cov=apps --cov=core --cov=agents \
		--cov=services --cov=repositories --cov=models --cov-report=term-missing \
		--cov-report=xml:coverage.xml --cov-fail-under=84

format:
	cd $(ENGINE_DIR) && .venv/bin/ruff format . ../scripts/*.py

lint:
	cd $(ENGINE_DIR) && .venv/bin/ruff format --check . ../scripts/*.py
	cd $(ENGINE_DIR) && .venv/bin/ruff check . ../scripts/*.py
	node --check MyAgent-Web/app.js
	node --check MyAgent-Web/sw.js
	node --check MyAgent-Studio/main.cjs
	node --check MyAgent-Studio/preload.cjs

typecheck:
	cd $(ENGINE_DIR) && .venv/bin/mypy core apps agents services repositories models tests ../scripts/*.py

security:
	cd $(ENGINE_DIR) && .venv/bin/bandit -q -r apps core agents services repositories models
	cd $(ENGINE_DIR) && .venv/bin/pip-audit --strict

openapi:
	$(PY) scripts/generate-openapi.py

generated-check: openapi
	git diff --exit-code -- docs/openapi.json

check: lint typecheck coverage security generated-check

compose-config:
	docker compose config --quiet

start:
	docker compose up --build -d

stop:
	docker compose down

logs:
	docker compose logs -f engine web

smoke:
	./scripts/smoke-test.sh

benchmark:
	cd $(ENGINE_DIR) && .venv/bin/python ../scripts/benchmark-engine.py

package:
	./scripts/package-release.sh

clean:
	rm -rf release $(ENGINE_DIR)/.coverage $(ENGINE_DIR)/coverage.xml
	find . -type d \( -name __pycache__ -o -name .pytest_cache -o -name .mypy_cache -o -name .ruff_cache \) -prune -exec rm -rf {} +
