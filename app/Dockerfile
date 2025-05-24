FROM python:3.9-slim

# Build argument for target architecture
ARG TARGETARCH=amd64
# Build argument for Gunicorn workers
ARG GUNICORN_WORKERS=2

# Fixed Chrome and ChromeDriver version (Selenium 4.x 호환 버전)
ENV CHROME_VERSION="136.0.7103.113"
ENV CHROME_DRIVER_VERSION="136.0.7103.113"

# System environment variable to reflect the target architecture for any runtime scripts if needed
ENV APP_TARGETARCH=${TARGETARCH}
# Environment variable for Gunicorn workers, set from the build argument
ENV GUNICORN_WORKERS=${GUNICORN_WORKERS}

# Install common system packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    unzip \
    ca-certificates \
    fonts-noto-cjk \
    fontconfig \
    libglib2.0-0 \
    libnss3 \
    libdbus-1-3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libexpat1 \
    libgbm1 \
    libasound2 \
    # Dependencies for WeasyPrint
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    libcairo2 \
    jq \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Chrome and ChromeDriver based on TARGETARCH
RUN \
    apt-get update && \
    # Add Google Chrome repository \
    wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-chrome.gpg && \
    echo "deb [arch=${TARGETARCH} signed-by=/usr/share/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list && \
    apt-get update && \
    # Install Chrome or Chromium based on TARGETARCH
    echo "BUILDING FOR TARGETARCH: ${TARGETARCH}" && \
    if [ "${TARGETARCH}" = "amd64" ]; then \
        # Install specific version of Chrome \
        wget -q "https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb" -O chrome.deb && \
        dpkg -i chrome.deb || true && \
        apt-get install -f -y && \
        rm chrome.deb && \
        # Pin Chrome version \
        echo "google-chrome-stable hold" | dpkg --set-selections && \
        # Install matching ChromeDriver version \
        wget -q "https://storage.googleapis.com/chrome-for-testing-public/${CHROME_VERSION}/linux64/chromedriver-linux64.zip" -O chromedriver.zip && \
        unzip chromedriver.zip && \
        mv chromedriver-linux64/chromedriver /usr/local/bin/chromedriver && \
        chmod +x /usr/local/bin/chromedriver && \
        rm -rf chromedriver.zip chromedriver-linux64 && \
        echo "Installed ChromeDriver version: ${CHROME_DRIVER_VERSION}" ; \
    elif [ "${TARGETARCH}" = "arm64" ]; then \
        # For arm64, use chromium from apt repository \
        apt-get install -y --no-install-recommends chromium chromium-driver && \
        # Pin chromium version \
        echo "chromium hold" | dpkg --set-selections && \
        echo "chromium-driver hold" | dpkg --set-selections && \
        # Create symlink for chromedriver \
        ln -sf /usr/bin/chromedriver /usr/local/bin/chromedriver ; \
    else \
        echo "Unsupported TARGETARCH for Chrome/Chromium installation: ${TARGETARCH}" && exit 1; \
    fi && \
    # Cleanup apt lists
    rm -rf /var/lib/apt/lists/*

# Set up application directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create upload directory
RUN mkdir -p /tmp/uploads

# Add cleanup script
COPY cleanup.py /app/cleanup.py
RUN chmod +x /app/cleanup.py

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5001/health || exit 1

# Expose port for Gunicorn
EXPOSE 5001

# Force Gunicorn with absolute path and ensure logs go to stdout/stderr
ENV PYTHONPATH=/app:$PYTHONPATH

# Create startup script
RUN echo '#!/bin/sh\n\
# Start cleanup script in background\n\
python /app/cleanup.py &\n\
# Start Gunicorn\n\
exec /usr/local/bin/gunicorn "$@"\n\
' > /app/start.sh && chmod +x /app/start.sh

ENTRYPOINT ["/app/start.sh"]
CMD ["--bind", "0.0.0.0:5001", "--workers", "2", "--log-level", "debug", "--access-logfile", "-", "--error-logfile", "-", "app:app"] 