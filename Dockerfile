FROM python:3.10-slim

WORKDIR /app

# Install build essentials
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency specifications
COPY pyproject.toml .
RUN pip install --no-cache-dir fastapi uvicorn pydantic numpy sentence-transformers tabulate

# Copy codebase
COPY . .
RUN pip install --no-cache-dir -e .

EXPOSE 8000

CMD ["uvicorn", "timemeshin.server.app:app", "--host", "0.0.0.0", "--port", "8000"]
