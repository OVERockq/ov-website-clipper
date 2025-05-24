from flask import Flask, request, send_file, render_template, Response, jsonify
from web_to_ebook import WebToEbook
import os
import tempfile
import json
import time
from threading import Thread
import queue
import zipfile
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import logging # Add logging import
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

app = Flask(__name__)

# Configure basic logging
logging.basicConfig(level=logging.DEBUG)

# Translations
translations = {
    'ko': {
        'title': "웹페이지 변환 마법사 - EPUB, PDF, Markdown 변환",
        'meta_description': "웹페이지를 EPUB, Markdown, DOCX, PDF 등 다양한 형식으로 손쉽게 변환하세요. 여러 페이지 병합, 번역 기능도 지원합니다.",
        'meta_keywords': "웹페이지 변환, ebook 변환, HTML 변환, EPUB, Markdown, DOCX, PDF, 온라인 변환기, 웹 콘텐츠 저장",
        'logo_text_part1': "WebTo",
        'logo_text_part2': "Ebook",
        'header_subtitle': "원하는 웹페이지를 손쉽게 EPUB, PDF, Markdown 등 다양한 파일로 변환하세요!",
        'step1_title': "URL 입력",
        'step2_title': "변환 영역 선택",
        'step3_title': "변환 옵션",
        'step4_title': "완료",
        'url_input_label': "웹페이지 URL",
        'url_input_placeholder': "https://example.com",
        'url_input_help': "변환하고 싶은 웹페이지의 전체 URL을 입력해주세요.",
        'conversion_scope_label': "웹페이지에서 변환할 영역을 어떻게 선택하시겠어요?",
        'scope_single_page': "단일 페이지 (자동인식/읽기모드)",
        'scope_multiple_pages': "여러 페이지 (직접 선택자 입력)",
        'selectors_info': "여러 페이지 변환 시 아래 선택자를 정확히 입력해주세요.",
        'content_selector_label': "본문 선택자",
        'content_selector_placeholder': "예: main, #content, //div[@class='article-body']",
        'content_selector_help_intro': "각 페이지에서 실제 내용이 담긴 영역입니다. CSS 선택자 또는 XPath.",
        'content_selector_help_example': "예: <code>main</code>, <code>.article-content</code>",
        'menu_selector_label': "메뉴 선택자",
        'menu_selector_placeholder': "예: nav, .sidebar ul, //div[@class='table-of-contents']",
        'menu_selector_help_intro': "여러 페이지 링크가 포함된 메뉴 영역입니다. CSS 선택자 또는 XPath.",
        'menu_selector_help_example': "예: <code>nav ul.menu</code>, <code>#toc</code>",
        'output_format_label': "출력 형식",
        'merge_pages_label': "페이지 병합",
        'merge_pages_yes': "하나의 문서로 병합",
        'merge_pages_no': "개별 문서로 생성",
        'merge_pages_help': "Markdown 개별 생성 시 ZIP으로 제공됩니다.",
        'translation_option_label': "번역 옵션",
        'translation_language_label': "번역 언어",
        'font_family_label': "글꼴 (PDF/DOCX 용)",
        'confirm_and_convert_title': "Step 4: 확인 및 변환",
        'summary_title': "입력 정보 요약:",
        'summary_help': '정보가 정확한지 확인 후 "변환 시작" 버튼을 눌러주세요.',
        'loading_text': "변환 중입니다. 잠시 기다려주세요...",
        'progress_text_template': "{progress}% ({current_page}/{total_pages} 페이지)",
        'conversion_complete_title': "변환이 완료되었습니다!",
        'download_prompt': "아래 버튼으로 다운로드하세요.",
        'download_button': "다운로드",
        'error_prefix': "오류:",
        'error_title': "변환 실패",
        'retry_button': "다시 시도",
        'previous_button': "이전",
        'next_button': "다음",
        'submit_button': "변환 시작",
        'copyright_notice_title': "저작권 유의사항",
        'copyright_notice_text': "본 서비스를 통해 변환된 콘텐츠의 저작권은 원저작자에게 있습니다. 사용자는 개인적인 학습 및 연구 목적으로만 변환된 콘텐츠를 사용해야 하며, 저작권법을 위반하는 방식으로 사용하거나 무단으로 배포, 공유, 상업적으로 이용해서는 안 됩니다. 본 서비스는 사용자가 제공한 URL의 웹 콘텐츠를 기술적으로 변환하는 도구이며, 콘텐츠의 내용이나 저작권에 대한 책임을 지지 않습니다. 서비스 이용으로 인해 발생하는 모든 법적 책임은 사용자 본인에게 있습니다.",
        'ads_area_title': "광고",
        'bottom_ad_placeholder': "하단 광고가 표시될 영역입니다.",
        'right_ad_placeholder': "오른쪽 광고 영역",
        'right_ad_size_info': "(160x600 또는 유사 크기 권장)",
        'footer_copyright': "&copy; 2024 WebToEbook. All rights reserved.",
        'footer_rate_limit_info': "변환 제한: 분당 {rate_limit_convert_per_minute}회, 시간당 {rate_limit_per_hour}회, 일일 {rate_limit_per_day}회.",
        'validate_required': "이 필드는 필수입니다.",
        'validate_url': "유효한 URL을 입력해주세요 (예: http:// 또는 https://).",
        'error_network_unknown': "네트워크 또는 알 수 없는 오류: {message}"
    },
    'en': {
        'title': "Web Page Converter Wizard - EPUB, PDF, Markdown",
        'meta_description': "Easily convert web pages to various formats like EPUB, Markdown, DOCX, PDF. Supports merging multiple pages and translation features.",
        'meta_keywords': "web page converter, ebook converter, HTML converter, EPUB, Markdown, DOCX, PDF, online converter, save web content",
        'logo_text_part1': "WebTo",
        'logo_text_part2': "Ebook",
        'header_subtitle': "Easily convert your desired web pages into various files like EPUB, PDF, Markdown!",
        'step1_title': "Enter URL",
        'step2_title': "Select Conversion Area",
        'step3_title': "Conversion Options",
        'step4_title': "Complete",
        'url_input_label': "Web Page URL",
        'url_input_placeholder': "https://example.com",
        'url_input_help': "Please enter the full URL of the web page you want to convert.",
        'conversion_scope_label': "How would you like to select the area to convert from the web page?",
        'scope_single_page': "Single Page (Auto-detect/Read Mode)",
        'scope_multiple_pages': "Multiple Pages (Manual Selector Input)",
        'selectors_info': "For multiple page conversion, please enter the selectors below accurately.",
        'content_selector_label': "Content Selector",
        'content_selector_placeholder': "e.g., main, #content, //div[@class='article-body']",
        'content_selector_help_intro': "The area containing the actual content on each page. CSS selector or XPath.",
        'content_selector_help_example': "e.g., <code>main</code>, <code>.article-content</code>",
        'menu_selector_label': "Menu Selector",
        'menu_selector_placeholder': "e.g., nav, .sidebar ul, //div[@class='table-of-contents']",
        'menu_selector_help_intro': "The menu area containing links to multiple pages. CSS selector or XPath.",
        'menu_selector_help_example': "e.g., <code>nav ul.menu</code>, <code>#toc</code>",
        'output_format_label': "Output Format",
        'merge_pages_label': "Merge Pages",
        'merge_pages_yes': "Merge into a single document",
        'merge_pages_no': "Create individual documents",
        'merge_pages_help': "Individual Markdown files will be provided as a ZIP.",
        'translation_option_label': "Translation Option",
        'translation_language_label': "Translation Language",
        'font_family_label': "Font (for PDF/DOCX)",
        'confirm_and_convert_title': "Step 4: Confirm and Convert",
        'summary_title': "Summary of Input Information:",
        'summary_help': 'Please verify the information is correct, then press the "Start Conversion" button.',
        'loading_text': "Converting. Please wait a moment...",
        'progress_text_template': "{progress}% ({current_page}/{total_pages} pages)",
        'conversion_complete_title': "Conversion Complete!",
        'download_prompt': "Download using the button below.",
        'download_button': "Download",
        'error_prefix': "Error:",
        'error_title': "Conversion Failed",
        'retry_button': "Try Again",
        'previous_button': "Previous",
        'next_button': "Next",
        'submit_button': "Start Conversion",
        'copyright_notice_title': "Copyright Notice",
        'copyright_notice_text': "The copyright of the content converted through this service belongs to the original author. Users should use the converted content for personal learning and research purposes only, and must not use it in a manner that violates copyright law, or distribute, share, or use it commercially without authorization. This service is a tool that technically converts web content from the URL provided by the user, and is not responsible for the content or its copyright. All legal responsibilities arising from the use of the service lie with the user.",
        'ads_area_title': "Advertisement",
        'bottom_ad_placeholder': "Bottom ad area.",
        'right_ad_placeholder': "Right ad area",
        'right_ad_size_info': "(160x600 or similar size recommended)",
        'footer_copyright': "&copy; 2024 WebToEbook. All rights reserved.",
        'footer_rate_limit_info': "Conversion limits: {rate_limit_convert_per_minute}/min, {rate_limit_per_hour}/hr, {rate_limit_per_day}/day.",
        'validate_required': "This field is required.",
        'validate_url': "Please enter a valid URL (e.g., http:// or https://).",
        'error_network_unknown': "Network or unknown error: {message}"
    }
}

def get_locale():
    # Priority: URL parameter, then Accept-Language header, then default 'ko'
    lang = request.args.get('lang')
    if lang and lang in translations:
        return lang
    # For simplicity, not parsing Accept-Language header for now, can be added later
    return 'ko' # Default language

# 업로드된 파일을 저장할 디렉토리
UPLOAD_FOLDER = '/tmp/uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# 번역 API 키 환경변수
DISABLE_TRANSLATION = os.environ.get('DISABLE_TRANSLATION', 'false').lower() == 'true'

PAPAGO_CLIENT_ID = None
PAPAGO_CLIENT_SECRET = None
OPENAI_API_KEY = None
DEEPL_API_KEY = None

if not DISABLE_TRANSLATION:
    PAPAGO_CLIENT_ID = os.environ.get('PAPAGO_CLIENT_ID')
    PAPAGO_CLIENT_SECRET = os.environ.get('PAPAGO_CLIENT_SECRET')
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    DEEPL_API_KEY = os.environ.get('DEEPL_API_KEY')

# 광고 ID 환경변수
AD_CLIENT_ID = os.environ.get('AD_CLIENT_ID')

# 진행 상황을 저장할 전역 변수
progress_data = {
    'current_page': 0,
    'total_pages': 0,
    'progress': 0,
    'completed': False,
    'error': None
}

# Flask-Limiter 설정
# 환경 변수에서 요청 제한 값을 읽어오거나 기본값을 사용합니다.
RATE_LIMIT_PER_DAY = os.environ.get('RATE_LIMIT_PER_DAY', "200")
RATE_LIMIT_PER_HOUR = os.environ.get('RATE_LIMIT_PER_HOUR', "50")
RATE_LIMIT_CONVERT_PER_MINUTE = os.environ.get('RATE_LIMIT_CONVERT_PER_MINUTE', "10")

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=[f"{RATE_LIMIT_PER_DAY} per day", f"{RATE_LIMIT_PER_HOUR} per hour"],
    storage_uri="memory://",
)

# 진행 상황 업데이트를 위한 큐
progress_queue = queue.Queue()

def update_progress(current, total, error=None):
    """진행 상황을 업데이트합니다."""
    progress = int((current / total) * 100) if total > 0 else 0
    progress_data['current_page'] = current
    progress_data['total_pages'] = total
    progress_data['progress'] = progress
    progress_data['completed'] = current >= total if total > 0 else False
    progress_data['error'] = error
    progress_queue.put(progress_data.copy())

@app.route('/')
def index():
    lang_code = get_locale()
    app.logger.debug(f"Selected lang_code: {lang_code}")
    # Ensure trans is always a dictionary, even if lang_code is somehow invalid (should not happen with current get_locale)
    trans = translations.get(lang_code, translations.get('en', {})) 
    app.logger.debug(f"Translations for lang_code '{lang_code}': {type(trans)} - Keys (first few): {list(trans.keys())[:5] if trans else 'None'}")
    
    if not trans:
        app.logger.error(f"Critical: Translations not found for lang_code '{lang_code}'. Fallback did not work.")
        # Fallback to English or an empty dict to prevent UndefinedError, though the page will be broken.
        trans = translations.get('en', {}) # Or provide a minimal default structure

    return render_template(
        'index.html', 
        disable_translation=DISABLE_TRANSLATION,
        ad_client_id=AD_CLIENT_ID,
        rate_limit_per_day=RATE_LIMIT_PER_DAY,
        rate_limit_per_hour=RATE_LIMIT_PER_HOUR,
        rate_limit_convert_per_minute=RATE_LIMIT_CONVERT_PER_MINUTE,
        translations=trans, # Pass translations to the template
        current_lang=lang_code # Pass current language to template
    )

@app.route('/api/available_translators')
def available_translators():
    translators = []
    if not DISABLE_TRANSLATION:
        translators.append({'value': 'none', 'label': '번역하지 않음'})
        # 브라우저 내장 번역 옵션 추가
        translators.append({'value': 'browser', 'label': '브라우저 내장 번역 사용'})
        if PAPAGO_CLIENT_ID and PAPAGO_CLIENT_SECRET:
            translators.append({'value': 'papago', 'label': 'Papago API'})
        if OPENAI_API_KEY:
            translators.append({'value': 'gpt', 'label': 'GPT API'})
        if DEEPL_API_KEY:
            translators.append({'value': 'deepl', 'label': 'DeepL API'})
    else:
        # 번역 비활성화 시 "번역하지 않음" 옵션만 제공하거나, 아예 빈 리스트를 반환할 수 있습니다.
        # 여기서는 "번역하지 않음"을 기본값처럼 동작하게 하기 위해 이 옵션을 추가합니다.
        translators.append({'value': 'none', 'label': '번역하지 않음 (비활성화됨)'})
    return jsonify(translators)

@app.route('/progress')
def progress():
    """Server-Sent Events 엔드포인트"""
    def generate():
        try:
            while True:
                try:
                    data = progress_queue.get(timeout=5)  # 타임아웃 감소
                    if data.get('completed') or data.get('error'):
                        yield f"data: {json.dumps(data)}\n\n"
                        break
                    yield f"data: {json.dumps(data)}\n\n"
                except queue.Empty:
                    yield ": keepalive\n\n"
        except GeneratorExit:
            # 클라이언트 연결 종료 시 정리
            app.logger.info("Client disconnected from progress stream")
        except Exception as e:
            app.logger.error(f"Error in progress stream: {str(e)}")
            yield f"data: {json.dumps({'error': 'Progress stream error'})}\n\n"
    return Response(generate(), mimetype='text/event-stream')

def create_driver():
    try:
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-software-rasterizer')
        
        # ChromeDriver 자동 설치 및 버전 관리
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver
    except Exception as e:
        app.logger.error(f"Driver creation error: {str(e)}")
        raise

@app.route('/convert', methods=['POST'])
@limiter.limit(f"{RATE_LIMIT_CONVERT_PER_MINUTE} per minute")
def convert():
    output_path = None
    try:
        url = request.form['url']
        conversion_scope = request.form.get('conversion_scope', 'single')
        
        content_selector = request.form.get('content_selector', '')
        menu_selector = request.form.get('menu_selector', '')

        if conversion_scope == 'single':
            content_selector = "__AUTO_SINGLE_PAGE__"
            menu_selector = None

        output_format = request.form['output_format']
        target_lang = request.form.get('target_lang', '')
        merge_pages = request.form.get('merge_pages', 'true').lower() == 'true'
        translator_type = request.form.get('translator_type', 'none')
        font_family = request.form.get('font_family', 'Noto Sans KR')

        # 입력값 검증
        if not url or not url.startswith(('http://', 'https://')):
            raise ValueError("유효한 URL을 입력해주세요.")

        driver = create_driver()

        converter = WebToEbook(
            title="",
            base_url=url,
            content_selector=content_selector,
            menu_selector=menu_selector,
            translator_type=translator_type,
            target_lang=target_lang,
            papago_id=PAPAGO_CLIENT_ID,
            papago_secret=PAPAGO_CLIENT_SECRET,
            openai_key=OPENAI_API_KEY,
            deepl_key=DEEPL_API_KEY,
            font_family=font_family
        )

        output_dir = '/tmp/uploads'
        os.makedirs(output_dir, exist_ok=True)
        
        actual_output_format_extension = "md" if output_format.lower() == "markdown" else output_format
        temp_filename = f"ebook_conversion_{int(time.time())}.{actual_output_format_extension}"
        output_path = os.path.join(output_dir, temp_filename)

        def conversion_process_wrapper():
            nonlocal output_path
            try:
                converter.process(output_path=output_path, output_format=output_format)
                time.sleep(0.5)  # 파일 시스템 동기화 대기

                if not os.path.exists(output_path):
                    raise FileNotFoundError("변환된 파일이 생성되지 않았습니다.")

                # 파일명 생성
                base_filename_url = url.replace("https://", "").replace("http://", "")
                safe_base_filename = re.sub(r"[^a-zA-Z0-9-_]", "_", base_filename_url)
                safe_base_filename = re.sub(r"_+", "_", safe_base_filename).strip('_')

                doc_title = converter.title if converter.title else ""
                if doc_title:
                    safe_title = re.sub(r"[^a-zA-Z0-9-_ ]", "", doc_title).strip().replace(" ", "_")
                    final_base_name = safe_title if safe_title else safe_base_filename
                else:
                    final_base_name = safe_base_filename

                download_extension = "md" if output_format.lower() == "markdown" else output_format
                if target_lang and translator_type != 'none':
                    final_download_name = f"{final_base_name}_{target_lang}.{download_extension}"
                else:
                    final_download_name = f"{final_base_name}.{download_extension}"

                return final_download_name

            except Exception as e:
                app.logger.error(f"Conversion error: {str(e)}")
                update_progress(0, 0, str(e))
                raise

        thread = Thread(target=conversion_process_wrapper)
        thread.start()
        thread.join()

        if output_path and os.path.exists(output_path):
            try:
                final_download_name = conversion_process_wrapper()
                response = send_file(
                    output_path,
                    as_attachment=True,
                    download_name=final_download_name
                )
                return response
            except Exception as e:
                app.logger.error(f"File sending error: {str(e)}")
                raise
        else:
            raise FileNotFoundError("변환된 파일을 찾을 수 없습니다.")

    except Exception as e:
        app.logger.error(f"Conversion endpoint error: {str(e)}")
        error_message = "변환 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
        return jsonify({'error': error_message}), 500
    finally:
        if 'driver' in locals():
            driver.quit()
        # 임시 파일 정리
        if output_path and os.path.exists(output_path):
            try:
                os.remove(output_path)
                app.logger.info(f"Temporary file removed: {output_path}")
            except Exception as e:
                app.logger.error(f"Failed to remove temporary file: {str(e)}")

@app.route('/health')
def health_check():
    """Health check endpoint for Docker container."""
    return jsonify({
        'status': 'healthy',
        'timestamp': time.time()
    }), 200
