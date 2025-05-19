from flask import Flask, request, send_file, render_template, Response, jsonify
from web_to_ebook import WebToEbook
import os
import tempfile
import json
import time
from threading import Thread
import queue
import zipfile

app = Flask(__name__)

# 업로드된 파일을 저장할 디렉토리
UPLOAD_FOLDER = '/tmp/uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# 번역 API 키 환경변수
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
    return render_template('index.html')

@app.route('/api/available_translators')
def available_translators():
    translators = []
    translators.append({'value': 'none', 'label': '번역하지 않음'})
    translators.append({'value': 'browser', 'label': '내장 브라우저'})
    if PAPAGO_CLIENT_ID and PAPAGO_CLIENT_SECRET:
        translators.append({'value': 'papago', 'label': 'Papago API'})
    if OPENAI_API_KEY:
        translators.append({'value': 'gpt', 'label': 'GPT API'})
    if DEEPL_API_KEY:
        translators.append({'value': 'deepl', 'label': 'DeepL API'})
    return jsonify(translators)

@app.route('/progress')
def progress():
    """Server-Sent Events 엔드포인트"""
    def generate():
        while True:
            try:
                data = progress_queue.get(timeout=30)  # 30초 타임아웃
                yield f"data: {json.dumps(data)}\n\n"
            except queue.Empty:
                break
    return Response(generate(), mimetype='text/event-stream')

@app.route('/convert', methods=['POST'])
def convert():
    output_path = None
    try:
        url = request.form['url']
        title = request.form['title']
        content_selector = request.form['content_selector']
        menu_selector = request.form.get('menu_selector', '')
        output_format = request.form['output_format']
        target_lang = request.form.get('target_lang', '')
        merge_pages = request.form.get('merge_pages', 'true').lower() == 'true'
        translator_type = request.form.get('translator_type', 'browser')
        txt_content = None
        if 'txt_file' in request.files:
            file = request.files['txt_file']
            if file.filename:
                txt_content = file.read().decode('utf-8')
        font_family = request.form.get('font_family', 'Noto Sans KR')
        converter = WebToEbook(
            title=title,
            base_url=url,
            content_selector=content_selector,
            menu_selector=menu_selector if menu_selector else None,
            txt_content=txt_content,
            translator_type=translator_type,
            papago_id=PAPAGO_CLIENT_ID,
            papago_secret=PAPAGO_CLIENT_SECRET,
            openai_key=OPENAI_API_KEY,
            deepl_key=DEEPL_API_KEY,
            font_family=font_family
        )
        output_dir = '/tmp/uploads'
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f'converted_document.{output_format}')
        
        def conversion_process():
            nonlocal output_path
            try:
                if menu_selector:
                    menu_links = converter.get_menu_links()
                    total_pages = len(menu_links)
                    update_progress(0, total_pages)
                    for i, link in enumerate(menu_links, 1):
                        page_content = converter.get_page_content(link)
                        if page_content:
                            converter.pages.append({
                                'title': link.split('/')[-1],
                                'content': page_content
                            })
                        update_progress(i, total_pages)
                elif txt_content:
                    pages = converter.process_txt_content()
                    total_pages = len(pages)
                    update_progress(0, total_pages)
                    for i, page in enumerate(pages, 1):
                        converter.pages.append({
                            'title': f'페이지 {i}',
                            'content': f'<div>{page}</div>'
                        })
                        update_progress(i, total_pages)
                else:
                    update_progress(0, 1)
                    main_content = converter.get_page_content()
                    converter.pages.append({
                        'title': title,
                        'content': main_content
                    })
                    update_progress(1, 1)
                
                if target_lang and converter.pages and translator_type != 'browser' and translator_type != 'none':
                    total_pages = len(converter.pages)
                    update_progress(0, total_pages)
                    for i, page in enumerate(converter.pages, 1):
                        page['content'] = converter.translate_html_text(page['content'], target_lang, translator_type)
                        update_progress(i, total_pages)
                
                if merge_pages:
                    combined_content = ''
                    for page in converter.pages:
                        combined_content += f"<h1>{page['title']}</h1>\n{page['content']}\n"
                    if output_format == 'epub':
                        converter.create_epub(combined_content, output_path)
                    elif output_format == 'markdown':
                        converter.create_markdown(combined_content, output_path)
                    elif output_format == 'doc':
                        converter.create_doc(combined_content, output_path)
                    elif output_format == 'pdf':
                        converter.create_pdf(combined_content, output_path)
                else:
                    if output_format == 'markdown':
                        zip_path = output_path.replace('.md', '.zip')
                        with zipfile.ZipFile(zip_path, 'w') as zipf:
                            for i, page in enumerate(converter.pages, 1):
                                page_path = os.path.join(output_dir, f'page_{i}.md')
                                if output_format == 'epub':
                                    converter.create_epub(page['content'], page_path)
                                elif output_format == 'markdown':
                                    converter.create_markdown(page['content'], page_path)
                                elif output_format == 'doc':
                                    converter.create_doc(page['content'], page_path)
                                elif output_format == 'pdf':
                                    converter.create_pdf(page['content'], page_path)
                                zipf.write(page_path, f'page_{i}.{output_format}')
                                os.remove(page_path)
                        output_path = zip_path
                    else:
                        for i, page in enumerate(converter.pages, 1):
                            page_path = os.path.join(output_dir, f'page_{i}.{output_format}')
                            if output_format == 'epub':
                                converter.create_epub(page['content'], page_path)
                            elif output_format == 'markdown':
                                converter.create_markdown(page['content'], page_path)
                            elif output_format == 'doc':
                                converter.create_doc(page['content'], page_path)
                            elif output_format == 'pdf':
                                converter.create_pdf(page['content'], page_path)
                update_progress(len(converter.pages), len(converter.pages))
            except Exception as e:
                print(f"변환 중 오류 발생: {str(e)}")
                output_path = None
                raise
                
        thread = Thread(target=conversion_process)
        thread.start()
        thread.join()
        
        if output_path and os.path.exists(output_path):
        return send_file(
            output_path,
            as_attachment=True,
                download_name=f'converted_document.{output_format}'
        )
        else:
            return '파일 생성 실패', 500
    except Exception as e:
        return str(e), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True) 