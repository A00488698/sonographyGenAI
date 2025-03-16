from flask import Flask, request, send_file, jsonify
from werkzeug.utils import secure_filename
import os
from docx import Document
from fpdf import FPDF
import pytesseract
from pydub import AudioSegment
import speech_recognition as sr
from pdfminer.high_level import extract_text
from docx import Document as DocxDocument
import google.generativeai as genai  # 引入 Google Generative AI 库
import logging
import uuid
import json
from dotenv import load_dotenv
from pathlib import Path

from flask_cors import CORS

app = Flask(__name__, static_folder='../frontend', template_folder='../frontend')
CORS(app)  # 启用 CORS 支持
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

logging.basicConfig(level=logging.DEBUG)

# 添加认证文件路径检查
credentials_path = Path('backend/gen-lang-client-0067690517-2d914e495b91.json')
if not credentials_path.exists():
    raise FileNotFoundError(f"认证文件不存在: {credentials_path}")

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = str(credentials_path)

def process_image(filepath):
    """使用 Tesseract OCR 处理图片"""
    try:
        from PIL import Image
        
        img = Image.open(filepath)
        text = pytesseract.image_to_string(img, lang='chi_sim')
        return text.strip() or "未识别到文字"
    except Exception as e:
        logging.error(f"图片处理失败: {str(e)}")
        return ""

def process_audio(filepath):
    # 将音频转换为文本
    recognizer = sr.Recognizer()
    audio = AudioSegment.from_wav(filepath)
    audio.export("temp.wav", format="wav")
    with sr.AudioFile("temp.wav") as source:
        audio_data = recognizer.record(source)
        text = recognizer.recognize_google(audio_data, language="zh-CN")
    return text

def process_text(filepath):
    # 直接读取文本文件
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

def process_pdf(filepath):
    # 使用 pdfminer 提取文本
    text = extract_text(filepath)
    return text

def process_docx(filepath):
    # 读取 docx 文件内容
    doc = DocxDocument(filepath)
    text = '\n'.join([para.text for para in doc.paragraphs])
    return text

def generate_report(data, format='docx', report_id=None):
    # 生成报告
    if format == 'docx':
        doc = Document('backend/templates/template1.docx')  # 使用模板文件
        # 替换模板中的占位符
        for paragraph in doc.paragraphs:
            for key, value in data.items():
                if f'{{{key}}}' in paragraph.text:
                    paragraph.text = paragraph.text.replace(f'{{{key}}}', value)
        report_path = f'reports/{report_id}.docx' if report_id else 'clinical_report.docx'
        doc.save(report_path)
    elif format == 'pdf':
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        for key, value in data.items():
            pdf.cell(200, 10, txt=f"{key}: {value}", ln=True)
        report_path = f'reports/{report_id}.pdf' if report_id else 'clinical_report.pdf'
        pdf.output(report_path)
    return report_path

def call_gemini_model(text):
    try:
        model = genai.GenerativeModel('gemini-pro')
        prompt = f"请根据以下临床笔记生成结构化报告：\n{text}\n\n报告应包括以下字段：\n- 患者姓名 (patient_name)\n- 检查日期 (examination_date)\n- 性别 (sex)\n- 年龄 (age)\n- 参考医生 (refby)\n- UHID 号 (uhidno)\n- 检查类型 (examination_type)\n- 检查区域 (examined_area)\n- 设备型号 (device_model)\n- 影像发现 (imaging_findings)\n- 诊断总结 (diagnosis_summary)\n- 评论 (Comment)"
        response = model.generate_content(prompt)
        structured_data = {}
        for line in response.text.split('\n'):
            if '：' in line:
                key, value = line.split('：', 1)
                structured_data[key.strip()] = value.strip()
        required_fields = ['patient_name', 'examination_date', 'sex', 'age', 'refby', 'uhidno', 'examination_type', 'examined_area', 'device_model', 'imaging_findings', 'diagnosis_summary', 'Comment']
        for field in required_fields:
            if field not in structured_data:
                structured_data[field] = ''
        return structured_data
    except Exception as e:
        logging.error(f'Error calling Gemini API: {str(e)}')
        return None

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/<path:filename>')
def static_files(filename):
    return app.send_static_file(filename)

@app.route('/process', methods=['POST'])
def process_file():
    logging.debug('Received file upload request')
    if 'file' not in request.files:
        logging.error('No file uploaded')
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    file_type = request.form.get('type', 'text')
    
    if file.filename == '':
        logging.error('No file selected')
        return jsonify({'error': 'No file selected'}), 400
    
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    logging.debug(f'Saved file to {filepath}')
    
    try:
        if file_type == 'audio':
            if filename.endswith('.wav') or filename.endswith('.mp3'):
                text = process_audio(filepath)
            else:
                logging.error('Unsupported audio format')
                return jsonify({'error': 'Unsupported audio format'}), 400
        else:
            if filename.endswith('.jpg') or filename.endswith('.jpeg'):
                text = process_image(filepath)
            elif filename.endswith('.pdf'):
                text = process_pdf(filepath)
            elif filename.endswith('.docx'):
                text = process_docx(filepath)
            elif filename.endswith('.txt'):
                text = process_text(filepath)
            else:
                logging.error('Unsupported file type')
                return jsonify({'error': 'Unsupported file type'}), 400
        
        logging.debug('Calling Google Gemini API')
        structured_data = call_gemini_model(text)
        
        # 生成报告 ID
        report_id = str(uuid.uuid4())
        # 确保 reports 目录存在
        os.makedirs('reports', exist_ok=True)
        report_path = generate_report(structured_data, 'docx', report_id)
        
        return jsonify({
            'reportId': report_id,
            'downloadUrl': f'/download/{report_id}'  # 修改下载URL格式
        }), 200
    except Exception as e:
        logging.error(f'Error processing file: {str(e)}')
        return jsonify({'error': f'Error processing file: {str(e)}'}), 500

@app.route('/download/<report_id>', methods=['GET'])
def download_report(report_id):
    try:
        # 构建报告文件路径
        report_path = os.path.join('reports', f'{report_id}.docx')
        
        # 检查文件是否存在
        if not os.path.exists(report_path):
            return jsonify({'error': '报告不存在'}), 404
            
        return send_file(report_path, as_attachment=True)
    except Exception as e:
        logging.error(f'下载报告失败: {str(e)}')
        return jsonify({'error': f'下载报告失败: {str(e)}'}), 500

if __name__ == '__main__':
    # 确保上传目录和报告目录存在
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs('reports', exist_ok=True)
    app.run(debug=True) 