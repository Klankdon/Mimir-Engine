# ==========================================
# STAGE 1: Build Svelte 5 + Vite 8 Frontend
# ==========================================
FROM node:22-alpine AS frontend-builder

WORKDIR /app

# Copy package manifests first to leverage Docker layer caching
COPY package*.json ./

# Clean install node dependencies
RUN npm ci

# Copy full repository source and build static dist/ bundle
COPY . .
RUN npm run build

# ==========================================
# STAGE 2: Python 3.11 Runtime + FastAPI
# ==========================================
FROM python:3.11-slim

# Prevent .pyc files & enable live stdout/stderr logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install minimal system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend Python application code
COPY . .

# Copy compiled Svelte static assets from Stage 1 into /app/dist
COPY --from=frontend-builder /app/dist ./dist

# Create storage folder with appropriate ownership for bind mounts
RUN mkdir -p /app/storage

# Expose internal engine port
EXPOSE 59056

# Non-root user setup for security isolation
RUN useradd -m mimiruser && chown -R mimiruser:mimiruser /app
USER mimiruser

# Launch FastAPI via Uvicorn
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "59056"]
