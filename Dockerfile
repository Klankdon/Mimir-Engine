# ==========================================
# STAGE 1: Build Svelte 5 + Vite 8 Frontend
# ==========================================
FROM node:22-alpine AS frontend-builder
WORKDIR /build

# Copy frontend manifests and install
COPY mimir-desktop/package*.json ./
RUN npm ci

# Copy frontend source and build
COPY mimir-desktop/ .
RUN npm run build

# ==========================================
# STAGE 2: Python 3.11 Runtime + FastAPI
# ==========================================
FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends build-essential libpq-dev curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Copy compiled Svelte assets from builder into the root /app/dist
COPY --from=frontend-builder /build/dist ./dist

RUN mkdir -p /app/storage
EXPOSE 59056
RUN useradd -m mimiruser && chown -R mimiruser:mimiruser /app
USER mimiruser

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "59056"]
