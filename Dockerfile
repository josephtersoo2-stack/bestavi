# Stage 1: Build React Frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: Production Python Application
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

# Install system dependencies (PostgreSQL client libraries, curl)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY backend/ ./backend/
COPY aviator_bot/ ./aviator_bot/
COPY config/ ./config/

# Copy compiled React frontend assets from Stage 1
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

WORKDIR /app/backend

# Create staticfiles directory
RUN mkdir -p staticfiles

EXPOSE 8000

CMD ["sh", "-c", "python manage.py migrate --noinput && python -m daphne -b 0.0.0.0 -p ${PORT:-8000} config.asgi:application"]
