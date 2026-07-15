FROM python:3.12-slim AS builder

ENV VIRTUAL_ENV=/opt/venv \
    PIP_DISABLE_PIP_VERSION_CHECK=1
RUN python -m venv "$VIRTUAL_ENV"
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

WORKDIR /build
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir --requirement requirements.txt

FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    PORT=8000

RUN groupadd --system myagent \
    && useradd --system --gid myagent --home-dir /app myagent \
    && mkdir -p /app/data \
    && chown -R myagent:myagent /app
WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
COPY --chown=myagent:myagent . .
USER myagent

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD python -c "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:'+os.getenv('PORT','8000')+'/api/v1/health/ready', timeout=3)" || exit 1
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn apps.backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
