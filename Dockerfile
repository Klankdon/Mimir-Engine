FROM node:22-alpine AS frontend-builder
WORKDIR /build
COPY mimir-desktop/package*.json ./
RUN npm ci
COPY mimir-desktop/ .
RUN npm run build

FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends build-essential libpq-dev curl && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
COPY --from=frontend-builder /build/dist ./dist
RUN mkdir -p /app/storage
EXPOSE 59056
RUN useradd -m mimiruser && chown -R mimiruser:mimiruser /app
USER mimiruser
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "59056"]
