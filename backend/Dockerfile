# One image, two commands: API (uvicorn) and worker (python -m src.workers.main).
# The command is chosen per-service in docker-compose.yml.
FROM python:3.12-slim

WORKDIR /app
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install dependencies first (cached until pyproject changes).
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e .

COPY src ./src

EXPOSE 8000
CMD ["uvicorn", "src.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
