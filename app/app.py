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

app = Flask(__name__)

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

# 진행 상황을 저장할 전역 변수
progress_data = {
    'current_page': 0,
    'total_pages': 0,
    'progress': 0
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

def update_progress(current, total):
    """진행 상황을 업데이트합니다."""
    progress = int((current / total) * 100) if total > 0 else 0
    progress_data['current_page'] = current
    progress_data['total_pages'] = total
    progress_data['progress'] = progress
    progress_queue.put(progress_data)

@app.route('/')
def index():
    return render_template('index.html', disable_translation=DISABLE_TRANSLATION)

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
        while True:
            try:
                data = progress_queue.get(timeout=15)  # 타임아웃을 줄여서 더 자주 체크
                yield f"data: {json.dumps(data)}\n\n"
            except queue.Empty:
                # 연결 유지를 위해 주석(comment) 형태의 keep-alive 메시지를 보냅니다.
                yield ": keepalive\n\n"
                # 루프를 계속하여 다음 메시지를 기다립니다.
                # 만약 특정 조건에서 완전히 종료해야 한다면, 그 조건을 명시적으로 처리해야 합니다.
                # 예를 들어, 변환 작업 완료 후 특정 신호를 받으면 break 하도록 할 수 있습니다.
                # 현재는 무한 루프로 두어 클라이언트가 연결을 유지하도록 합니다.
                # 실제 프로덕션 환경에서는 더 정교한 연결 관리 로직이 필요할 수 있습니다.
                continue 
    return Response(generate(), mimetype='text/event-stream')

@app.route('/convert', methods=['POST'])
@limiter.limit(f"{RATE_LIMIT_CONVERT_PER_MINUTE} per minute") # 변환 요청에 대한 추가 제한
def convert():
    output_path = None
    try:
        url = request.form['url']
        conversion_scope = request.form.get('conversion_scope', 'single') # 'single' or 'multiple'
        
        content_selector = request.form.get('content_selector', '')
        menu_selector = request.form.get('menu_selector', '')

        if conversion_scope == 'single':
            # 단일 페이지 모드일 경우, content_selector를 특별한 값으로 설정하거나 비워둠
            # web_to_ebook.py에서 이 값을 보고 자동 처리하도록 유도
            content_selector = "__AUTO_SINGLE_PAGE__" # 예시 특별 값
            menu_selector = None # 단일 페이지 모드에서는 메뉴 선택자 사용 안함
        # 'multiple' 모드에서는 사용자가 입력한 값을 그대로 사용

        output_format = request.form['output_format']
        target_lang = request.form.get('target_lang', '')
        merge_pages = request.form.get('merge_pages', 'true').lower() == 'true'
        translator_type = request.form.get('translator_type', 'none')
        font_family = request.form.get('font_family', 'Noto Sans KR')
        converter = WebToEbook(
            title="",
            base_url=url,
            content_selector=content_selector,
            menu_selector=menu_selector,
            translator_type=translator_type,
            target_lang=target_lang, # target_lang 인자 추가
            papago_id=PAPAGO_CLIENT_ID,
            papago_secret=PAPAGO_CLIENT_SECRET,
            openai_key=OPENAI_API_KEY,
            deepl_key=DEEPL_API_KEY,
            font_family=font_family
        )
        output_dir = '/tmp/uploads'
        os.makedirs(output_dir, exist_ok=True)
        
        # Markdown 확장자를 .md로 통일
        actual_output_format_extension = "md" if output_format.lower() == "markdown" else output_format
        temp_filename = f"ebook_conversion_placeholder.{actual_output_format_extension}"
        output_path = os.path.join(output_dir, temp_filename)

        final_download_name = "downloaded_file"

        def conversion_process_wrapper():
            nonlocal output_path
            nonlocal final_download_name
            nonlocal actual_output_format_extension # 함수 내에서 사용하기 위해 nonlocal 선언
            try:
                # process 메소드 호출 시 target_lang 인자 제거
                converter.process(output_path=output_path, output_format=output_format) # process에는 원래 output_format 전달
                
                # 파일 시스템 동기화를 위한 짧은 대기 시간 추가
                time.sleep(0.5) 

                if not os.path.exists(output_path):
                    app.logger.warning(f"os.path.exists 검사 실패: {output_path}. 파일이 실제로 생성되었는지 다시 확인합니다.")
                    # 만약 파일이 실제로 생성되었지만 exists가 즉시 True를 반환하지 않는 경우를 대비
                    # 이 부분은 근본적인 해결책은 아니지만, 간헐적인 파일 시스템 지연 문제에 대한 임시 방편이 될 수 있음
                    # 실제로는 converter.process가 성공/실패 여부를 명확히 반환하는 것이 좋음
                    if not os.path.exists(output_path): # 한 번 더 검사
                        raise FileNotFoundError(f"변환된 파일이 지정된 경로에 생성되지 않았습니다: {output_path}")

                doc_title = converter.title if converter.title else "converted_document"
                safe_title = "".join(c if c.isalnum() or c in (' ', '-', '_') else '' for c in doc_title).rstrip()
                
                # Add language suffix if translation was performed
                # 다운로드 파일명 확장자도 .md로 통일
                download_extension = "md" if output_format.lower() == "markdown" else output_format
                if target_lang and translator_type != 'none': # target_lang은 convert 함수의 지역 변수
                    final_download_name = f"{safe_title}_{target_lang}.{download_extension}"
                else:
                    final_download_name = f"{safe_title}.{download_extension}"

            except Exception as e:
                app.logger.error(f"변환 스레드 내 오류: {repr(e)}")
                output_path = None
                raise
                
        thread = Thread(target=conversion_process_wrapper)
        thread.start()
        thread.join()
        
        if output_path and os.path.exists(output_path):
            try:
                response = send_file(
                    output_path,
                    as_attachment=True,
                    download_name=final_download_name
                )
                return response
            finally:
                # 파일 전송 후 임시 파일 삭제
                if os.path.exists(output_path):
                    try:
                        os.remove(output_path)
                        app.logger.info(f"임시 파일 삭제 완료: {output_path}")
                    except Exception as e_remove:
                        app.logger.error(f"임시 파일 삭제 중 오류 발생: {output_path}, {e_remove}")
        else:
            app.logger.error(f"파일 생성 실패 또는 최종 경로 없음. output_path: {output_path}")
            return '파일 생성 실패', 500
    except Exception as e:
        # output_path가 None이 아니고, 예외 발생 전 파일이 생성되었을 수 있으므로 여기서도 삭제 시도
        if output_path and os.path.exists(output_path):
            try:
                os.remove(output_path)
                app.logger.info(f"오류 발생으로 인한 임시 파일 삭제: {output_path}")
            except Exception as e_remove_err:
                app.logger.error(f"오류 발생 후 임시 파일 삭제 중 오류: {output_path}, {e_remove_err}")
        app.logger.error(f"/convert 엔드포인트 오류: {repr(e)}")
        return str(e), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
