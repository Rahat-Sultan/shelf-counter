# Container image for hosting the app (livemy.app, Render, a VPS, or any Docker host).
# Debian 12 "bookworm" is pinned on purpose: on newer Debian, libglib2.0-0 was renamed, which breaks this install.
FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# ffmpeg re-encodes videos to H.264 for the browser. libgl1 and libglib2.0-0 are needed by the desktop
# OpenCV build that the inference package installs; without them, "import cv2" fails with libGL.so.1.
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Installed before copying the code, so code changes do not reinstall everything (about 1.5 GB).
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Run as a normal user. The app writes to /app/outputs and caches the model in the home folder.
RUN useradd --create-home app && chown -R app:app /app
USER app

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=120s \
    CMD python -c "import os, urllib.request; urllib.request.urlopen('http://localhost:' + os.environ.get('PORT', '8501') + '/_stcore/health')"

# Hosts that assign a port set PORT; otherwise 8501 is used.
CMD ["sh", "-c", "exec streamlit run app.py --server.port=${PORT:-8501} --server.address=0.0.0.0 --server.headless=true"]
