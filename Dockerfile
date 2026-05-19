# Stage 1: Build Environment
FROM python:3.12-slim AS builder

# Install system dependencies needed for compiling certain Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir virtualenv

# Create the virtual environment
ENV VIRTUAL_ENV=/opt/venv
RUN virtualenv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# Stage 2: Runtime Environment
FROM python:3.12-slim AS runner

# Copy the virtual environment from the builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN mkdir /data
ENV DUCKDB_DATABASE=/data/duckdb.db

# Set the working directory to /app
WORKDIR /app

# Copy the requirements file and the src directory into the container
COPY requirements.txt .
COPY src/ ./src/

# Expose the FastAPI port
EXPOSE 8000

# Run the application using the FastAPI CLI
CMD ["fastapi", "run", "src/main.py", "--host", "0.0.0.0", "--port", "8000"]