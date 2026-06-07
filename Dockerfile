FROM python:3.13-slim

WORKDIR /app

# Install dependencies as a separate layer so they're cached between code changes
COPY pyproject.toml .
RUN pip install --no-cache-dir .

COPY src/ ./src/

WORKDIR /app/src

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
