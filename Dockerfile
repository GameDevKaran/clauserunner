FROM python:3.11-slim

# Install Node.js for building React static assets inside container
RUN apt-get update && apt-get install -y curl && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy and compile frontend static assets
COPY frontend/package*.json ./frontend/
RUN cd frontend && npm install
COPY frontend/ ./frontend/
RUN cd frontend && npm run build

# Install Python backend requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt --prefer-binary

# Copy the remaining code (backend services, configs, etc.)
COPY . .

# Expose FastAPI container port
EXPOSE 8000

# Run FastAPI app
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
