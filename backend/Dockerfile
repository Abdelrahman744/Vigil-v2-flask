# ── Vigil Backend — Flask API ────────────────────────────────────────────
FROM python:3.12-slim

# Prevent Python from writing .pyc files & enable real-time stdout
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies first (cache-friendly layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Expose the API port
EXPOSE 5000

# Run with gunicorn in production (4 workers)
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "app:app"]
