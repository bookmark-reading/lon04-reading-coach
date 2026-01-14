# Use Python 3.13 as base image
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Copy uv from the official uv image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files
COPY pyproject.toml .
COPY .python-version .
COPY README.md .

# Copy source code
COPY src/ ./src/
COPY examples/ ./examples/
COPY resources/ ./resources/

# Install dependencies
RUN uv sync --no-dev

# Expose the API port
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DEBUG=false
ENV API_HOST=0.0.0.0
ENV API_PORT=8000

# Run the application using uvicorn
CMD ["uv", "run", "uvicorn", "src.application.api:app", "--host", "0.0.0.0", "--port", "8000"]
