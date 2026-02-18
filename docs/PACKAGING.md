# Packaging and Distribution Guide

This guide explains how to package OpsYield for Python (pip), Web UI (NPM), and Docker.

## 1. Python Package (`pip`)

The project is configured as a standard Python package.

### Prerequisites
- Python 3.10+
- `build` tool: `pip install build`

### Building the Package
To create a source distribution and wheel:

```bash
python -m build
```

This will create `dist/opsyield-x.y.z.tar.gz` and `dist/opsyield-x.y.z-py3-none-any.whl`.

### Installing Locally
```bash
pip install .
```

### Development Install (Editable)
```bash
pip install -e .
```

---

## 2. Web UI (NPM)

The Web UI is a React application built with Vite.

### Prerequisites
- Node.js 18+

### Building the Frontend
```bash
cd web-ui
npm install
npm run build
```

The build artifacts will be in `web-ui/dist`.

### Python Integration
To include the Web UI in the Python package (so `opsyield serve` serves the UI), you must copy the build artifacts to `opsyield/web/static`:

```bash
# From project root
mkdir -p opsyield/web/static
cp -r web-ui/dist/* opsyield/web/static/
```

After this, `pip install .` will include the UI files.

---

## 3. Docker Container

We provide a multi-stage Dockerfile that builds the frontend and installs the backend.

### Building the Image
```bash
docker build -t opsyield:latest .
```

### Running the Container
```bash
docker run -p 8000:8000 opsyield:latest
```

The application will be available at `http://localhost:8000`.

### Publishing to Docker Hub
```bash
docker tag opsyield:latest yourusername/opsyield:latest
docker push yourusername/opsyield:latest
```

---

## Troubleshooting

- **Missing UI**: If you see `{"message": "Frontend not found..."}` when accessing the root URL, it means the `opsyield/web/static` directory is missing or empty. Ensure you built the frontend and copied the assets (or used the Docker build which does this automatically).
