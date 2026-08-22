# Reproducible image for the S6E8 pipeline. Single stage by design —
# Implementation Plan §9 lists multi-stage builds and size optimisation as non-goals.
FROM python:3.11-slim

# PYTHONUNBUFFERED keeps the progress logging (CLAUDE.md §7a) streaming.
# PY overrides the Makefile's `PY ?= $(VENV)/bin/python`: there is no venv in here.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PY=python

# libgomp1: LightGBM's OpenMP runtime. make: not shipped in python:3.11-slim,
# and the default CMD is `make all`.
RUN apt-get update \
    && apt-get install --no-install-recommends -y libgomp1 make \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Dependency layer first, so it caches across source changes.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Non-root user. The output directories are created here because .dockerignore
# excludes data/, models/ and submissions/ from the build context.
RUN useradd --create-home --uid 1000 appuser \
    && mkdir -p data/raw data/processed models reports/figures submissions \
    && chown -R appuser:appuser /app
USER appuser

CMD ["make", "all"]
