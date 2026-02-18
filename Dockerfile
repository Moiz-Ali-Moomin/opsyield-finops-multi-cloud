# Stage 1: Build React Frontend
FROM node:20-alpine as frontend-builder

WORKDIR /app/web-ui

# Copy package files first for better caching
COPY web-ui/package.json web-ui/package-lock.json* ./

# Install dependencies
RUN npm ci

# Copy source code
COPY web-ui/ .

# Build the application (produces dist/)
RUN npm run build

# Stage 2: Python Backend
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies if required (e.g. for some python packages)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY . .

# Copy built frontend from Stage 1 to the location expected by main.py
# main.py expects: ../web/static relative to itself
# So if main.py is in /usr/local/lib/python3.11/site-packages/opsyield/api/main.py
# It expects /usr/local/lib/python3.11/site-packages/opsyield/web/static
#
# HOWEVER, we are installing the package. The package installation will include files 
# listed in MANIFEST.in. But the build artifacts are created in Stage 1, so they are 
# NOT in the source tree when `pip install .` runs (unless we copy them there first).
#
# STRATEGY: 
# 1. Copy dist to opsyield/web/static in the source tree.
# 2. Run pip install .
# 3. This ensures the static files are bundled into the installed package.

COPY --from=frontend-builder /app/web-ui/dist ./opsyield/web/static

# Install the package
RUN pip install .

# Create a non-root user for security
RUN useradd -m appuser
USER appuser

# Expose port
EXPOSE 8000

# Run the application
# We use the console script entry point defined in setup.py
CMD ["opsyield", "serve", "--host", "0.0.0.0", "--port", "8000"]
