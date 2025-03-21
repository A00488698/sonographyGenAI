from flask import Flask, request, send_file, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import os
import uuid
from pathlib import Path
import logging
from flask_cors import CORS
from dotenv import load_dotenv
from vosk import Model, KaldiRecognizer
import wave

# Import the three modules
from text_processing import process_image, process_audio, process_text, process_pdf, process_docx
from ai_processing import generate_report_with_ai, enhance_text_with_ai
from report_generation import generate_report, download_report

# -------------- 1. Get absolute path of project root directory --------------
BASE_DIR = Path(__file__).parent.parent.absolute()

# -------------- 2. Load environment variables (.env) --------------
load_dotenv(BASE_DIR / ".env")

# -------------- 3. Configure Flask's static and template directories --------------
app = Flask(
    __name__,
    static_folder=str(BASE_DIR / 'static'),
    template_folder=str(BASE_DIR / 'template')
)
CORS(app)

# -------------- 4. Configuration parameters: upload directory etc. --------------
UPLOAD_FOLDER = 'uploads'  # Note this is a relative path, will create/use uploads/ under TESTGEN/
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# -------------- 5. Configure logging --------------
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.FileHandler('app.log'),   # Log to file
        logging.StreamHandler()           # Log to console
    ]
)

# -------------------- Route definitions --------------------

# -------------- Homepage: Return template/index.html --------------
@app.route('/')
def index():
    return send_from_directory(app.template_folder, 'index.html')

# -------------- Text upload page: Return text-upload.html --------------
@app.route('/text-upload')
def text_upload():
    return send_from_directory(app.template_folder, 'text-upload.html')

# -------------- Audio upload page: Return audio-upload.html --------------
@app.route('/audio-upload')
def audio_upload():
    return send_from_directory(app.template_folder, 'audio-upload.html')

# -------------------- File upload processing and report generation --------------------

@app.route('/process', methods=['POST'])
def process_file():
    """
    Process uploaded file, perform OCR / speech recognition / text reading / PDF extraction based on file type,
    then call AI to generate structured report, finally generate report files (both DOCX and PDF formats),
    and return JSON response containing download links.
    """
    try:
        # 1. Check if file is uploaded
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'Invalid file'}), 400

        # 2. Save uploaded file to TESTGEN/uploads/
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # 3. Select processor based on file extension
        ext = filename.split('.')[-1].lower()
        processors = {
            'jpg': process_image,
            'jpeg': process_image,
            'png': process_image,
            'wav': process_audio,
            'mp3': process_audio,
            'pdf': process_pdf,
            'docx': process_docx,
            'txt': process_text
        }
        
        if ext not in processors:
            return jsonify({'error': 'Unsupported file type'}), 400
        
        text = processors[ext](filepath)
        
        # 4. Call Llama2 AI to generate structured report data
        structured_data = generate_report_with_ai(enhance_text_with_ai(text))
        print("Structured data from AI:", structured_data)
        if not structured_data:
            return jsonify({'error': 'AI report generation failed'}), 500
        
        # 5. Generate report files and store in TESTGEN/reports/
        report_id = str(uuid.uuid4())
        os.makedirs('reports', exist_ok=True)
        # Generate both DOCX and PDF versions
        original_filename = secure_filename(file.filename)
        docx_path = generate_report(structured_data, 'docx', report_id, original_filename)
        pdf_path = generate_report(structured_data, 'pdf', report_id, original_filename)
        
        # 6. Return report ID, download links for both formats and generated structured data
        return jsonify({
            'reportId': report_id,
            'downloadUrl_docx': f'/download/{report_id}?format=docx',
            'downloadUrl_pdf': f'/download/{report_id}?format=pdf',
            'data': structured_data
        }), 200
        
    except Exception as e:
        logging.error(f"Processing failed: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/download/<report_id>', methods=['GET'])
def download_report_route(report_id):
    """
    Find corresponding docx or pdf report file in TESTGEN/reports/ based on report_id and return to client for download
    """
    return download_report(report_id)

# -------------------- 404 error handling --------------------

@app.errorhandler(404)
def page_not_found(e):
    """
    When accessing non-existent route or file, return TESTGEN/template/404.html
    """
    return send_from_directory(app.template_folder, '404.html'), 404

# -------------------- Main function startup --------------------

if __name__ == '__main__':
    # 1. Check if necessary files exist (index.html / text-upload.html / audio-upload.html / 404.html)
    required_files = [
        BASE_DIR / 'template' / 'index.html',
        BASE_DIR / 'template' / 'text-upload.html',
        BASE_DIR / 'template' / 'audio-upload.html',
        BASE_DIR / 'template' / '404.html'
    ]
    for file_path in required_files:
        if not file_path.exists():
            logging.critical(f"Critical file missing: {file_path}")
            exit(1)
    
    # 2. Create necessary directories: uploads/ and reports/
    Path('uploads').mkdir(exist_ok=True)
    Path('reports').mkdir(exist_ok=True)
    
    # 3. Start Flask server, listen on 0.0.0.0:5000
    app.run(host='0.0.0.0', port=5000, debug=True) 