# OV Website Clipper

웹 페이지를 다양한 형식의 전자책으로 변환하는 웹 애플리케이션입니다. EPUB, PDF, Word (DOCX), Markdown 등 다양한 형식을 지원하며, 다중 페이지 변환, 자동 목차 생성, 읽기 모드 최적화, 다국어 번역 (한국어/영어 지원) 및 API를 통한 번역 기능을 제공합니다.

## 주요 기능

- **다양한 출력 형식 지원**: EPUB, PDF, Word (DOCX), Markdown
- **다중 페이지 변환**: 메뉴/사이드바 기반 자동 수집 또는 단일 페이지 변환
- **자동 목차 생성** (지원 형식에 따라)
- **읽기 모드 최적화**: 불필요한 요소(광고, 메뉴, 푸터 등) 제거, 가독성 향상
- **다국어 UI 지원**: 한국어, 영어 (URL 파라미터 `?lang=ko` 또는 `?lang=en`로 전환)
- **콘텐츠 번역 지원**:
  - 내장 브라우저 번역 (Selenium Chrome)
  - Papago API
  - GPT API
  - DeepL API
- **요청 빈도 제한**: 안정적인 서비스 운영을 위한 요청 수 제한 기능
- **Docker 기반 배포**: Docker Compose를 사용한 간편한 배포 및 운영 환경 구성 (Gunicorn 사용)

## 설치 및 실행 방법

### 권장: Docker 사용 (Docker Compose)

이 방법은 프로덕션 환경에 권장되며, Gunicorn을 사용하여 애플리케이션을 실행합니다.

1.  **저장소 클론**:
    ```bash
    git clone https://github.com/OVERockq/ov-website-clipper.git
    cd ov-website-clipper
    ```

2.  **환경 변수 설정**:
    필요한 경우, `docker-compose.yml` 파일 내의 `environment` 섹션을 수정하여 번역 API 키 및 기타 설정을 변경합니다. (아래 '환경 변수 설정' 참고)

3.  **Docker 이미지 빌드 및 컨테이너 실행**:
    ```bash
    docker-compose up --build -d
    ```

4.  **애플리케이션 접속**:
    웹 브라우저에서 `http://localhost:5005` (또는 `docker-compose.yml`에서 설정한 포트)로 접속합니다.

### 로컬 직접 설치 (개발용)

1.  **저장소 클론**:
    ```bash
    git clone https://github.com/OVERockq/ov-website-clipper.git # 또는 개인 fork 경로
    cd ov-website-clipper
    ```

2.  **가상환경 생성 및 활성화**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # Windows: venv\Scripts\activate
    ```

3.  **의존성 설치**:
    `app` 디렉토리로 이동하여 `requirements.txt` 파일의 의존성을 설치합니다.
    ```bash
    cd app
    pip install -r requirements.txt
    ```

4.  **환경 변수 설정** (필요시):
    터미널에서 직접 설정하거나 `.env` 파일(python-dotenv 라이브러리 필요)을 사용할 수 있습니다.

5.  **애플리케이션 실행**:
    `app` 디렉토리 내에서 Flask 개발 서버를 직접 실행합니다.
    ```bash
    python app.py
    ```
    이 경우, Gunicorn 없이 Flask 개발 서버로 실행되며, 기본적으로 `http://localhost:5001`로 접속합니다.

## 환경 변수 설정

`docker-compose.yml` 파일의 `web` 서비스 `environment` 섹션에서 다음 변수들을 설정할 수 있습니다. 로컬 직접 실행 시에는 시스템 환경 변수로 설정합니다.

- **번역 API 키**:
  - `DISABLE_TRANSLATION`: `true`로 설정 시 모든 번역 기능 비활성화 (기본값: `false`)
  - `PAPAGO_CLIENT_ID`: Papago API 클라이언트 ID
  - `PAPAGO_CLIENT_SECRET`: Papago API 클라이언트 시크릿
  - `OPENAI_API_KEY`: OpenAI API 키
  - `DEEPL_API_KEY`: DeepL API 키 (Free 또는 Pro)

- **광고 ID** (웹 UI에 광고를 표시할 경우):
  - `AD_CLIENT_ID_RIGHT`: 오른쪽 사이드바 광고 클라이언트 ID
  - `AD_SLOT_ID_RIGHT`: 오른쪽 사이드바 광고 슬롯 ID
  - `AD_CLIENT_ID_BOTTOM`: 하단 광고 클라이언트 ID
  - `AD_SLOT_ID_BOTTOM`: 하단 광고 슬롯 ID

- **요청 빈도 제한**:
  - `RATE_LIMIT_PER_DAY`: 일일 총 요청 제한 (기본값: 200)
  - `RATE_LIMIT_PER_HOUR`: 시간당 총 요청 제한 (기본값: 50)
  - `RATE_LIMIT_CONVERT_PER_MINUTE`: 분당 변환 요청 제한 (기본값: 10)

## 환경 설정

### 광고 설정
Google AdSense를 사용하기 위해서는 다음 환경 변수를 설정해야 합니다:

1. `.env` 파일 생성:
```bash
# .env 파일 생성
touch .env
```

2. `.env` 파일에 다음 내용 추가:
```env
# Google AdSense Configuration
AD_CLIENT_ID=ca-pub-XXXXXXXXXXXXXXXX  # 실제 AdSense 클라이언트 ID로 교체

# Translation Settings
DISABLE_TRANSLATION=true

# Rate Limiting
RATE_LIMIT_PER_DAY=200
RATE_LIMIT_PER_HOUR=50
RATE_LIMIT_CONVERT_PER_MINUTE=10
```

3. Docker Compose 실행:
```bash
docker-compose up -d
```

### 환경 변수 설명
- `AD_CLIENT_ID`: Google AdSense 클라이언트 ID (예: ca-pub-XXXXXXXXXXXXXXXX)
- `DISABLE_TRANSLATION`: 번역 기능 비활성화 (true/false)
- `RATE_LIMIT_*`: API 요청 제한 설정

## 사용 방법

1.  웹 브라우저에서 애플리케이션에 접속합니다 (Docker 사용 시 `http://localhost:5005`).
2.  페이지 우측 상단에서 언어(한국어/English)를 선택할 수 있습니다.
3.  변환할 웹페이지의 URL을 입력합니다.
4.  변환 영역 선택:
    - **단일 페이지 (자동인식/읽기모드)**: 현재 URL의 페이지만 변환하며, 가독성을 위해 콘텐츠를 자동 추출합니다.
    - **여러 페이지 (직접 선택자 입력)**: 여러 페이지를 하나의 문서로 병합할 때 사용합니다. 본문 내용과 메뉴(목차) 링크가 포함된 영역의 CSS 선택자 또는 XPath를 입력합니다.
5.  변환 옵션 설정:
    - **출력 형식**: EPUB, Markdown, Word (DOCX), PDF 중 선택합니다.
    - **페이지 병합**: 여러 페이지 변환 시 하나의 문서로 병합할지, 개별 문서로 생성할지 선택합니다 (Markdown 개별 생성 시 ZIP으로 제공).
    - **번역 옵션**: 번역을 원할 경우 번역기와 대상 언어를 선택합니다 (API 키 설정 필요).
    - **글꼴**: PDF/DOCX 형식 출력 시 사용할 글꼴을 선택합니다.
6.  입력 정보를 확인하고 "변환 시작" 버튼을 클릭합니다.
7.  변환이 진행되는 동안 진행 상황이 표시됩니다.
8.  완료되면 다운로드 버튼이 활성화되어 파일을 다운로드할 수 있습니다.

## 주요 기술 스택

- **백엔드**: Python, Flask, Selenium, BeautifulSoup
- **프론트엔드**: HTML, Tailwind CSS, JavaScript
- **서버**: Gunicorn (Docker 배포 시)
- **배포**: Docker, Docker Compose

## 주의사항

- 일부 웹사이트는 저작권 또는 기술적인 이유로 변환이 제한될 수 있습니다.
- API 키가 필요한 번역 옵션은 해당 키가 환경 변수로 제공되지 않으면 자동으로 비활성화되거나 선택 목록에 표시되지 않을 수 있습니다.
- 매우 크거나 복잡한 웹페이지, 또는 많은 수의 하위 페이지를 변환할 경우 시간이 다소 소요될 수 있으며 서버 리소스 사용량에 주의해야 합니다.
- 변환된 콘텐츠의 저작권은 원저작자에게 있으며, 사용자는 저작권법을 준수하여 개인적인 용도로만 사용해야 합니다.

## 라이선스

MIT License

## 기여하기

1.  이 저장소를 Fork합니다.
2.  새로운 기능 또는 버그 수정을 위한 브랜치를 생성합니다 (`git checkout -b feature/AmazingFeature` 또는 `bugfix/IssueNumber`).
3.  변경 사항을 커밋합니다 (`git commit -m 'Add some AmazingFeature'`).
4.  브랜치에 푸시합니다 (`git push origin feature/AmazingFeature`).
5.  Pull Request를 생성합니다.

버그 리포트나 기능 제안은 GitHub Issues를 통해 제출해주시면 감사하겠습니다. 