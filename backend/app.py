from flask import Flask, request, send_file, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import os
from docx import Document
from fpdf import FPDF
import pytesseract
from pydub import AudioSegment
import logging
import uuid
from pathlib import Path
from PIL import Image
from flask_cors import CORS
import json
from vosk import Model, KaldiRecognizer
import wave
from dotenv import load_dotenv
from docxtpl import DocxTemplate

# -------------- Added: Import transformers for Llama2 --------------
from transformers import pipeline

# -------------- 1. Get absolute path of project root directory --------------
# Assuming app.py is in backend directory, then:
# Path(__file__) => backend/app.py
# Path(__file__).parent => backend/
# Path(__file__).parent.parent => TESTGEN/
BASE_DIR = Path(__file__).parent.parent.absolute()

# -------------- 2. Load environment variables (.env) --------------
# .env file is placed under TESTGEN/, so use BASE_DIR / ".env"
load_dotenv(BASE_DIR / ".env")

# --------------------------------------------------
# -------------- 3. Configure Flask's static and template directories --------------
# static_folder points to TESTGEN/static
# template_folder points to TESTGEN/template
# --------------------------------------------------
app = Flask(
    __name__,
    static_folder=str(BASE_DIR / 'static'),
    template_folder=str(BASE_DIR / 'template')
)
CORS(app)

# -------------- 4. Configuration parameters: upload directory etc. --------------
UPLOAD_FOLDER = 'uploads'  # Note this is a relative path, will create/use uploads/ under TESTGEN/
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# -------------- 5. Initialize Vosk speech recognition models globally --------------
# model/ contains English and Chinese models
vosk_models = {
    'en': Model('model/vosk-model-small-en-us-0.15'),
    'cn': Model('model/vosk-model-small-cn-0.22')
}

# --------------------------------------------------
# -------------- 6. Initialize Llama2 model --------------
# Using Hugging Face transformers pipeline
# Note: Loading Llama2 model requires significant resources, recommended to run on GPU
# --------------------------------------------------
try:
    llama2_generator = pipeline("text-generation", model="gpt2", truncation=True)
except Exception as e:
    logging.error("Llama2 initialization failed: " + str(e))
    llama2_generator = None

# -------------- 7. Configure logging --------------
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
    # When accessing http://localhost:5000/, return TESTGEN/template/index.html
    return send_from_directory(app.template_folder, 'index.html')

# -------------- Text upload page: Return text-upload.html --------------
@app.route('/text-upload')
def text_upload():
    # When accessing http://localhost:5000/text-upload, return TESTGEN/template/text-upload.html
    return send_from_directory(app.template_folder, 'text-upload.html')

# -------------- Audio upload page: Return audio-upload.html --------------
@app.route('/audio-upload')
def audio_upload():
    # When accessing http://localhost:5000/audio-upload, return TESTGEN/template/audio-upload.html
    return send_from_directory(app.template_folder, 'audio-upload.html')

# -------------- Static files (CSS/JS/images etc.) --------------
# Flask will automatically serve files under TESTGEN/static via /static route
# So in HTML can use <link rel="stylesheet" href="/static/css/styles.css"> etc.

# -------------------- Business logic functions --------------------

def convert_audio(filepath):
    """Convert audio file to Vosk supported format: mono 16kHz 16-bit PCM"""
    try:
        audio = AudioSegment.from_file(filepath)
        audio = audio.set_channels(1).set_frame_rate(16000).set_sample_width(2)
        converted_path = Path(filepath).with_suffix('.wav')
        audio.export(converted_path, format="wav")
        return str(converted_path)
    except Exception as e:
        logging.error(f"Audio conversion failed: {str(e)}")
        raise

def process_image(filepath):
    """Process image using Tesseract OCR and return recognized text"""
    try:
        img = Image.open(filepath)
        text = pytesseract.image_to_string(img, lang='eng')  # Changed to English recognition
        return text.strip() or "No text recognized"
    except Exception as e:
        logging.error(f"Image processing failed: {str(e)}")
        return ""

def process_audio(filepath, language='en'):
    """Process audio using Vosk, select English or Chinese model based on language parameter"""
    try:
        filepath = convert_audio(filepath)  # First convert to WAV format
        model = vosk_models.get(language, vosk_models['en'])  # Default to English model
        
        wf = wave.open(filepath, "rb")
        if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getframerate() not in [8000, 16000]:
            raise ValueError("Audio format not supported, requires mono 16-bit PCM WAV format with 8000 or 16000 Hz sample rate")
        
        rec = KaldiRecognizer(model, wf.getframerate())
        result = ""
        
        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            if rec.AcceptWaveform(data):
                result += json.loads(rec.Result())["text"]
        
        return result.strip() or "No speech recognized"
    except Exception as e:
        logging.error(f"Audio processing failed: {str(e)}")
        return ""

def process_text(filepath):
    """Process plain text file, read and return content"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logging.error(f"Text processing failed: {str(e)}")
        return ""

def process_pdf(filepath):
    """Process PDF file using pdfminer and return extracted text"""
    try:
        from pdfminer.high_level import extract_text
        return extract_text(filepath)
    except Exception as e:
        logging.error(f"PDF processing failed: {str(e)}")
        return ""

def process_docx(filepath):
    """Process Word document using python-docx and return all paragraph text"""
    try:
        from docx import Document as DocxDocument
        doc = DocxDocument(filepath)
        return '\n'.join([para.text for para in doc.paragraphs])
    except Exception as e:
        logging.error(f"Word processing failed: {str(e)}")
        return ""


def generate_report(data, format='docx', report_id=None):
    """
    Generate report file using template1.docx template.
    First generate DOCX file, render placeholders in template using docxtpl.
    If format parameter is 'pdf', convert generated DOCX to PDF and return PDF file path.
    
    Parameters:
      data: AI generated structured data (dict), template placeholders correspond to keys:
            patient_name, examination_date, sex, age, refby, uhidno, examination_type, 
            examined_area, device_model, imaging_findings, diagnosis_summary, Comment
      format: 'docx' or 'pdf', default 'docx'
      report_id: Used to distinguish report filenames, if not provided use default filename
    
    Returns:
      Absolute path of generated report file
    """
    try:
        # Construct template file path: located at TESTGEN/backend/templates/template1.docx
        template_path = os.path.join(str(BASE_DIR / 'backend' / 'templates'), 'template1.docx')
        
        # Load template document using DocxTemplate
        doc = DocxTemplate(template_path)
        
        # Render template using docxtpl, data is context, template should contain following placeholders:
        # NAME{patient_name}
        # DATE{examination_date}
        # SEX{sex}
        # AGE: {age}
        # REF.BY{refby}
        # UHID NO: {uhidno}
        # Examination Type{examination_type}
        # Examined Area{examined_area}
        # Device Model{device_model}
        # Findings:{imaging_findings}
        # Diagnosis:{diagnosis_summary}
        # Comments:{Comment}
        doc.render(data)
        
        # Ensure reports directory exists, generate absolute path for report saving (DOCX format)
        reports_dir = BASE_DIR / 'reports'
        reports_dir.mkdir(exist_ok=True)
        docx_report_path = os.path.join(str(reports_dir), f'{report_id}.docx') if report_id else os.path.join(str(reports_dir), 'clinical_report.docx')
        
        # Save DOCX file
        doc.save(docx_report_path)
        
        if format == 'pdf':
            # If PDF is needed, use docx2pdf library for conversion
            try:
                from docx2pdf import convert as docx2pdf_convert
                # Construct target PDF file path
                pdf_report_path = os.path.join(str(reports_dir), f'{report_id}.pdf') if report_id else os.path.join(str(reports_dir), 'clinical_report.pdf')
                # Convert generated DOCX to PDF
                docx2pdf_convert(docx_report_path, pdf_report_path)
                return pdf_report_path
            except Exception as conv_e:
                logging.error(f"Failed to convert DOCX to PDF: {str(conv_e)}")
                raise conv_e
        else:
            # Return DOCX file path
            return docx_report_path
        
    except Exception as e:
        logging.error(f"Report generation failed: {str(e)}")
        raise


def generate_report_with_ai(text):
    """
    Generate structured report using Llama2
    text: Text obtained from OCR or speech recognition
    """
    try:
        if llama2_generator is None:
            raise ValueError("Llama2 generator not initialized")
        
        # Construct prompt, specifying required fields
        prompt = f"""Below is some content. Generate a structured report strictly in JSON format with exactly the following keys. If a field is not mentioned in the content, set its value to "UNKNOWN". Do not include any text or commentary outside of the JSON object.

Keys:
- patient_name
- examination_date
- sex
- age
- refby
- uhidno
- examination_type
- examined_area
- device_model
- imaging_findings
- diagnosis_summary
- Comment

Content:
{text}

Output only a valid JSON object.
"""
        
        # Call Llama2 to generate
        response = llama2_generator(prompt, max_length=800, do_sample=True, temperature=0.7)
        generated_text = response[0]['generated_text']
        print(f"generated_text111: {generated_text}")
        # Try to parse generated text as JSON
        try:
            return json.loads(generated_text)
        except json.JSONDecodeError:
            # If cannot parse as JSON, return raw string
            return {'raw_response': generated_text}
        
    except Exception as e:
        logging.error(f"Llama2 report generation failed: {str(e)}")
        # If AI generation fails, return default structure
        return {
            'patient_name': 'unknown',
            'examination_date': 'unknown',
            'sex': 'unknown',
            'age': 'unknown',
            'refby': 'unknown',
            'uhidno': 'unknown',
            'examination_type': 'unknown',
            'examined_area': 'unknown',
            'device_model': 'unknown',
            'imaging_findings': 'unknown',
            'diagnosis_summary': 'unknown',
            'comment': 'unknown'
        }

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
        structured_data = generate_report_with_ai(text)
        print(structured_data)
        if not structured_data:
            return jsonify({'error': 'AI report generation failed'}), 500
        
        # 5. Generate report files and store in TESTGEN/reports/
        report_id = str(uuid.uuid4())
        os.makedirs('reports', exist_ok=True)
        # Generate both DOCX and PDF versions
        docx_path = generate_report(structured_data, 'docx', report_id)
        pdf_path = generate_report(structured_data, 'pdf', report_id)
        
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
def download_report(report_id):
    """
    Find corresponding docx or pdf report file in TESTGEN/reports/ based on report_id and return to client for download
    """
    try:
        # Get requested format parameter, default to docx
        format = request.args.get('format', 'docx')
        
        # Construct file path
        reports_dir = str(BASE_DIR / 'reports')
        file_path = os.path.join(reports_dir, f'{report_id}.{format}')
        
        # Check if file exists
        if not os.path.exists(file_path):
            return jsonify({'error': 'Report does not exist'}), 404
        
        return send_file(file_path, as_attachment=True)
    except Exception as e:
        logging.error(f'Failed to download report: {str(e)}')
        return jsonify({'error': f'Failed to download report: {str(e)}'}), 500
    
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