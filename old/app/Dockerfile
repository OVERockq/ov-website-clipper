FROM python:3.9-slim

# 시스템 패키지 설치
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    fonts-noto-cjk \
    fontconfig \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

# Chrome 설치(Chrome 최신 버전용)
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-chrome.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*


# ChromeDriver 설치 (Chrome 136 버전용)
RUN wget -q "https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/136.0.7103.94/linux64/chromedriver-linux64.zip" \
    && unzip chromedriver-linux64.zip \
    && mv chromedriver-linux64/chromedriver /usr/local/bin/ \
    && chmod +x /usr/local/bin/chromedriver \
    && rm -rf chromedriver-linux64.zip chromedriver-linux64

# 작업 디렉

# 작업 디렉토리 설정
WORKDIR /app

# Python 패키지 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# 업로드 디렉토리 생성
RUN mkdir -p /tmp/uploads

# 포트 설정
EXPOSE 5001

# 실행 명령
CMD ["gunicorn", "--bind", "0.0.0.0:5001", "--workers", "4", "app:app"] 