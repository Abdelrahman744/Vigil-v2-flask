
FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable unbuffered output

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system build dependencies (needed for compiling some python packages)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir gunicorn python-dotenv

# Copy backend application code
COPY . .

# Ensure instance directory exists for SQLite
RUN mkdir -p /app/instance

EXPOSE 5000

# Run with Gunicorn in production
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "3", "--timeout", "120", "app:app"]
