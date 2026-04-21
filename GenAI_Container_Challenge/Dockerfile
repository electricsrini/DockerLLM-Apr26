# syntax=docker/dockerfile:1.7
# escape=\

###############################################################################
# Stage 1 – builder
# Install dependencies into an isolated prefix so nothing extra ends up in
# the final image.
###############################################################################
FROM python:3.12-slim AS builder

# Build-time best practice: fail fast on any error
SHELL ["/bin/sh", "-euxc", ""]

WORKDIR /build

# Copy only the dependency manifest first to maximise layer-cache hits.
COPY app/requirements.txt .

# Install pip-tools for reproducible installs, then install deps into /install.
# --no-compile: skip .pyc generation in builder (done in runtime stage).
# --prefix:     isolate into /install so we copy only what we need.
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip==24.3.1 && \
    pip install --prefix=/install --no-compile --no-warn-script-location \
        -r requirements.txt

###############################################################################
# Stage 2 – runtime
# Minimal image: only the app code + installed packages.
###############################################################################
FROM python:3.12-slim AS runtime

# ── Security hardening ──────────────────────────────────────────────────────
# 1. No interactive shell history leaks.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PATH="/install/bin:$PATH" \
    PYTHONPATH="/install/lib/python3.12/site-packages"

# 2. Create a dedicated non-root user & group (no login shell, no home dir).
RUN groupadd --gid 10001 appgroup && \
    useradd  --uid 10001 --gid appgroup \
             --no-create-home --shell /sbin/nologin appuser

WORKDIR /app

# 3. Copy only the installed packages from builder – not build tools.
COPY --from=builder /install /install

# 4. Copy application source.
COPY app/main.py .

# 5. Drop to non-root.
USER appuser

# Expose only the necessary port.
EXPOSE 8000

# ── Healthcheck ─────────────────────────────────────────────────────────────
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python - <<'EOF'
import urllib.request, sys
try:
    urllib.request.urlopen("http://localhost:8000/health", timeout=4)
    sys.exit(0)
except Exception:
    sys.exit(1)
EOF

# ── Entrypoint ───────────────────────────────────────────────────────────────
# --no-access-log keeps container logs clean; remove if you want request logs.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", \
     "--workers", "1", "--no-access-log"]
