FROM python:3.10-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy package and install
COPY pyproject.toml setup.py README.md LICENSE ./
COPY timemeshin/ ./timemeshin/
RUN pip install --no-cache-dir .

# Copy app files
COPY app.py ./
COPY dropzone/ ./cloud_dropzone/

EXPOSE 8000

CMD ["python", "app.py"]