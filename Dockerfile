# syntax=docker/dockerfile:1
#
# Python 3.14 auf Debian bookworm-slim (E29-1). CI nutzt python-version "3.14".
# Patch-Updates: Tag bei Bedarf anheben (z. B. 3.14.6-slim-bookworm).

FROM python:3.14-slim-bookworm AS builder

WORKDIR /build

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


FROM python:3.14-slim-bookworm AS runtime

WORKDIR /app

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# pg_dump fuer One-Click-Backup aus der Web-UI (E25-1)
RUN apt-get update \
    && apt-get install -y --no-install-recommends postgresql-client \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd --gid 1000 seiton \
    && useradd --uid 1000 --gid seiton --create-home --shell /usr/sbin/nologin seiton

COPY --from=builder /opt/venv /opt/venv
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY prompts/ ./prompts/
COPY alembic.ini .

RUN chown -R seiton:seiton /app

USER seiton

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
