# Open Source Documentation Contribution — OpenTelemetry Python Contrib

## Overview
- **Project:** [open-telemetry/opentelemetry-python-contrib](https://github.com/open-telemetry/opentelemetry-python-contrib) (CNCF / Linux Foundation)
- **Issue:** [Doc holes in FastAPI instrumentation #3301](https://github.com/open-telemetry/opentelemetry-python-contrib/issues/3301)
- **Pull Request:** [docs(fastapi): document env vars, trace propagation, websockets, and logging #4939](https://github.com/open-telemetry/opentelemetry-python-contrib/pull/4939)
- **Contributor:** Rut Vaghani (`rut0607`)

---

## Documentation Gaps Addressed

1. **SDK Environment Variables:** Clarified that general OpenTelemetry SDK variables (`OTEL_EXPORTER_OTLP_ENDPOINT`, `OTEL_SERVICE_NAME`, etc.) are configured separately from FastAPI-specific settings, adding links to standard SDK setup.
2. **Trace Context Propagation:** Documented automatic context propagation for incoming HTTP requests via ASGI middleware and configured propagators.
3. **WebSocket Support:** Confirmed and explicitly documented WebSocket tracing capabilities based on test coverage (`test_fastapi_instrumentation.py`).
4. **Log-Trace Correlation:** Added detailed guidance on enabling log-trace correlation using `OTEL_PYTHON_LOG_CORRELATION` alongside the logging instrumentation package.
5. **PyPI Discoverability:** Added a direct link to the PyPI package page for easier access and installation.

---

## Evidence / Files Included
- `README.md`: Summary of contribution and links.
- `fastapi_init_MODIFIED.py`: Copy of the modified documentation source file.
