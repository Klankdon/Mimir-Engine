FROM python:3.11-slim

# Prevent Python from writing .pyc files & enable unbuffered stdout for live docker logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies (build tools for psycopg2/pgvector if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Expose the non-standard internal engine port
EXPOSE 59056

# Create an unprivileged user for security isolation
RUN useradd -m mimiruser && chown -R mimiruser:mimiruser /app
USER mimiruser

# Launch FastAPI/NiceGUI via Uvicorn
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "59056"]
