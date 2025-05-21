FROM python:3.9-slim

# Build argument for target architecture
ARG TARGETARCH=amd64
# Build argument for Gunicorn workers
ARG GUNICORN_WORKERS=2

# System environment variable to reflect the target architecture for any runtime scripts if needed
ENV APP_TARGETARCH=${TARGETARCH}

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
    # Install Chrome \
    # Note: If google-chrome-stable is not available for your TARGETARCH (e.g., some specific arm64 distros), \
    # you might need to install chromium-browser or an alternative. \
    apt-get install -y --no-install-recommends google-chrome-stable && \
    CHROME_VERSION_FULL=$(google-chrome-stable --version) && \
    echo "Installed Chrome version: $CHROME_VERSION_FULL" && \
    \
    # Install ChromeDriver - Version 120.0.6099.109 is used as an example. \
    # YOU MUST ENSURE THIS CHROMEDRIVER VERSION MATCHES THE INSTALLED CHROME VERSION. \
    # Using Chrome for Testing (CfT) JSON endpoints to find the correct URL is recommended for robustness. \
    CHROME_DRIVER_VERSION="120.0.6099.109" && \
    echo "Attempting to install ChromeDriver version: $CHROME_DRIVER_VERSION" && \
    if [ "${TARGETARCH}" = "amd64" ]; then \
        CHROME_DRIVER_URL="https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/${CHROME_DRIVER_VERSION}/linux64/chromedriver-linux64.zip"; \
        CHROME_DRIVER_EXTRACT_PATH="chromedriver-linux64/chromedriver"; \
    elif [ "${TARGETARCH}" = "arm64" ]; then \
        CHROME_DRIVER_URL="https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/${CHROME_DRIVER_VERSION}/linux-arm64/chromedriver-linux-arm64.zip"; \
        CHROME_DRIVER_EXTRACT_PATH="chromedriver-linux-arm64/chromedriver"; \
    else \
        echo "Unsupported TARGETARCH: ${TARGETARCH} for ChromeDriver" && exit 1; \
    fi && \
    wget -q "${CHROME_DRIVER_URL}" -O chromedriver.zip && \
    unzip chromedriver.zip && \
    mv "${CHROME_DRIVER_EXTRACT_PATH}" /usr/local/bin/chromedriver && \
    chmod +x /usr/local/bin/chromedriver && \
    chromedriver --version && \
    rm -rf chromedriver.zip chromedriver-* && \
    # Clean up apt lists \
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

# Run application using Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5001", "--workers", "${GUNICORN_WORKERS}", "app:app"] 