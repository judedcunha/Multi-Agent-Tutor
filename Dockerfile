FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Phase 3 specific dependencies
RUN pip install --no-cache-dir \
    redis>=5.0.0 \
    psycopg2-binary>=2.9.0 \
    sqlalchemy>=2.0.0 \
    alembic>=1.12.0 \
    websockets>=11.0

# Copy application code
COPY src/ ./src/
COPY .env .env

# Create necessary directories
RUN mkdir -p logs data models lessons

# Expose port
EXPOSE 8000

# Start application
CMD ["uvicorn", "src.main_tutor:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
