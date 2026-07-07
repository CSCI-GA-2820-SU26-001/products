FROM python:3.12-slim

# Ensure Python output is sent straight to logs, no buffering
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

WORKDIR /app

# Install dependencies first for better layer caching
RUN python -m pip install --no-cache-dir --upgrade pip pipenv
COPY Pipfile Pipfile.lock ./
RUN pipenv install --system --deploy --ignore-pipfile

# Copy just what the running service needs
COPY wsgi.py .
COPY service ./service

# Run as a non-root user
RUN useradd --uid 1001 --create-home appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health').read()" || exit 1

CMD ["gunicorn", "--bind=0.0.0.0:8080", "--log-level=info", "wsgi:app"]
