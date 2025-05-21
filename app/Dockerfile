FROM python:3.9-slim

# Build argument for target architecture
ARG TARGETARCH=amd64
# Build argument for Gunicorn workers
ARG GUNICORN_WORKERS=2
# Build argument for ChromeDriver version.
# IMPORTANT: You MUST find the version of google-chrome-stable that gets installed
# for your TARGETARCH and then set this ARG to the corresponding ChromeDriver version.
# You can typically find compatible ChromeDriver versions here:
# https://googlechromelabs.github.io/chrome-for-testing/
# Example: If 'google-chrome-stable' installs version 126.0.6478.X, you'd use a CHROME_DRIVER_VERSION like 126.0.6478.126
ARG CHROME_DRIVER_VERSION="126.0.6478.126" # Update this to match your Chrome version!

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
    # Dependencies for WeasyPrint (ensure these are sufficient or add more if needed)
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    libcairo2 \
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
        apt-get install -y --no-install-recommends google-chrome-stable && \
        CHROME_VERSION_FULL=$(google-chrome-stable --version) && \
        echo "Installed Chrome version: $CHROME_VERSION_FULL (Note: ChromeDriver version ARG must match this!)" && \
        echo "Attempting to install ChromeDriver version: $CHROME_DRIVER_VERSION (set via ARG)" && \
        if [ -z "$CHROME_DRIVER_VERSION" ]; then \
            echo "Error: CHROME_DRIVER_VERSION ARG is not set for amd64." && exit 1; \
        fi && \
        CHROME_DRIVER_URL="https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/${CHROME_DRIVER_VERSION}/linux64/chromedriver-linux64.zip" && \
        CHROME_DRIVER_EXTRACT_PATH="chromedriver-linux64/chromedriver" && \
        wget -q "${CHROME_DRIVER_URL}" -O chromedriver.zip && \
        unzip chromedriver.zip && \
        mv "${CHROME_DRIVER_EXTRACT_PATH}" /usr/local/bin/chromedriver && \
        chmod +x /usr/local/bin/chromedriver && \
        echo "Manually installed amd64 ChromeDriver version:" && \
        chromedriver --version && \
        rm -rf chromedriver.zip chromedriver-* ; \
    elif [ "${TARGETARCH}" = "arm64" ]; then \
        apt-get install -y --no-install-recommends chromium chromium-driver || \
            (echo "Failed to install chromium and chromium-driver, trying older chromium-browser" && \
             apt-get install -y --no-install-recommends chromium-browser chromium-driver) && \
        CHROME_VERSION_FULL=$(chromium --version || chromium-browser --version) && \
        echo "Installed Chromium version for arm64 (via apt): $CHROME_VERSION_FULL" && \
        # Ensure the apt-installed chromedriver is used and report its version
        # Typically, chromium-driver from apt installs to /usr/bin/chromedriver
        if [ -f /usr/bin/chromedriver ]; then \
            # If /usr/local/bin/chromedriver exists from a previous bad run, remove it
            rm -f /usr/local/bin/chromedriver && \
            ln -s /usr/bin/chromedriver /usr/local/bin/chromedriver && \
            echo "Using arm64 chromium-driver from apt. Version:" && \
            chromedriver --version ; \
        else \
            echo "Error: chromium-driver not found at /usr/bin/chromedriver for arm64 after apt install." && exit 1; \
        fi && \
        echo "CHROME_DRIVER_VERSION ARG (${CHROME_DRIVER_VERSION}) is ignored for arm64 as apt provides a matched version." ; \
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

# Expose port for Gunicorn
EXPOSE 5001

# Force Gunicorn with absolute path and ensure logs go to stdout/stderr
ENV PYTHONPATH=/app:$PYTHONPATH
# CMD ["sh", "-c", "/usr/local/bin/gunicorn --bind 0.0.0.0:5001 --workers 2 --log-level debug --access-logfile - --error-logfile - app:app"]

ENTRYPOINT ["/usr/local/bin/gunicorn"]
CMD ["--bind", "0.0.0.0:5001", "--workers", "2", "--log-level", "debug", "--access-logfile", "-", "--error-logfile", "-", "app:app"] 