# OV Website Clipper

웹 페이지를 다양한 형식의 전자책으로 변환하는 도구입니다.

## 주요 기능

- 다양한 출력 형식 지원
  - EPUB
  - PDF
  - Word (DOCX)
  - Markdown
- 다중 페이지 변환 지원
  - 메뉴/사이드바 기반 자동 수집
  - 텍스트 파일 업로드 지원
- 자동 목차 생성
- 읽기 모드 최적화
  - 불필요한 요소 제거
  - 코드 블록, 이미지, 표, 인용구 보존
  - 가독성 향상
- 다국어 번역 지원
  - 내장 브라우저 번역
  - Papago API
  - GPT API
  - DeepL API

## 설치 방법

### Docker 사용

```bash
# 저장소 클론
git clone https://github.com/OVERockq/ov-website-clipper.git
cd ov-website-clipper

# Docker 이미지 빌드
docker build -t ov-website-clipper .

# 컨테이너 실행
docker run -p 5000:5000 ov-website-clipper
```

### 직접 설치

```bash
# 저장소 클론
git clone https://github.com/your-username/ov-website-clipper.git
cd ov-website-clipper

# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 애플리케이션 실행
python app.py
```

## 환경 변수 설정

번역 API를 사용하기 위해 다음 환경 변수를 설정하세요:

```bash
# Papago API
PAPAGO_CLIENT_ID=your_client_id
PAPAGO_CLIENT_SECRET=your_client_secret

# OpenAI API
OPENAI_API_KEY=your_api_key

# DeepL API
DEEPL_API_KEY=your_api_key
```

## 사용 방법

1. 웹 브라우저에서 `http://localhost:5000` 접속
2. 변환할 웹페이지 URL 입력
3. 변환 옵션 설정
   - 출력 형식 선택 (EPUB/PDF/DOCX/Markdown)
   - 콘텐츠 선택자 지정
   - 메뉴 선택자 지정 (선택사항)
   - 번역 옵션 선택
4. 변환 시작
5. 변환이 완료되면 파일 다운로드

## 주요 옵션 설명

### 콘텐츠 선택자
- CSS 선택자 또는 XPath 사용 가능
- 예: `article`, `main`, `//div[@class="content"]`

### 메뉴 선택자
- 다중 페이지 변환 시 사용
- 메뉴/사이드바의 CSS 선택자 또는 XPath 지정
- 예: `nav`, `//ul[@class="menu"]`

### 번역 옵션
- 번역하지 않음: 원본 그대로 변환
- 내장 브라우저: 셀레니움 기반 번역
- Papago API: 네이버 파파고 API 사용
- GPT API: OpenAI GPT API 사용
- DeepL API: DeepL API 사용

## 주의사항

- 일부 웹사이트는 변환이 제한될 수 있습니다
- API 키가 없는 번역 옵션은 자동으로 비활성화됩니다
- 대용량 웹페이지 변환 시 시간이 다소 소요될 수 있습니다

## 라이선스

MIT License

## 기여하기

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request 