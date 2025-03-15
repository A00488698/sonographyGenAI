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
from google.cloud import vision
import google.generativeai as genai  # 引入 Google Generative AI 库
import logging
import uuid

from flask_cors import CORS

app = Flask(__name__, static_folder='../frontend', template_folder='../frontend')
CORS(app)  # 启用 CORS 支持
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 设置 Google Cloud Vision 客户端
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'backend/alert-tiger-435215-k3-25df65601fe7.json'
client = vision.ImageAnnotatorClient()

# 设置 Google Generative AI API 密钥
genai.configure(api_key='YOUR_GEMINI_API_KEY')  # 替换为你的 Gemini API 密钥

logging.basicConfig(level=logging.DEBUG)

def process_image(filepath):
    # 使用 Google Cloud Vision API 提取文本
    with open(filepath, 'rb') as image_file:
        content = image_file.read()
    image = vision.Image(content=content)
    response = client.text_detection(image=image)
    texts = response.text_annotations
    if texts:
        return texts[0].description
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

def generate_report(data, format='docx'):
    # 生成报告
    if format == 'docx':
        doc = Document('backend/templates/template.docx')  # 使用模板文件
        # 替换模板中的占位符
        for paragraph in doc.paragraphs:
            for key, value in data.items():
                if f'{{{key}}}' in paragraph.text:
                    paragraph.text = paragraph.text.replace(f'{{{key}}}', value)
        report_path = 'clinical_report.docx'
        doc.save(report_path)
    elif format == 'pdf':
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        for key, value in data.items():
            pdf.cell(200, 10, txt=f"{key}: {value}", ln=True)
        report_path = 'clinical_report.pdf'
        pdf.output(report_path)
    return report_path

def call_gemini_model(text):
    # 调用 Google Gemini API 生成结构化报告
    model = genai.GenerativeModel('gemini-pro')
    prompt = f"请根据以下临床笔记生成结构化报告：\n{text}\n\n报告应包括以下字段：\n- 患者姓名 (patient_name)\n- 检查日期 (examination_date)\n- 性别 (sex)\n- 年龄 (age)\n- 参考医生 (refby)\n- UHID 号 (uhidno)\n- 检查类型 (examination_type)\n- 检查区域 (examined_area)\n- 设备型号 (device_model)\n- 影像发现 (imaging_findings)\n- 诊断总结 (diagnosis_summary)\n- 评论 (Comment)"
    response = model.generate_content(prompt)
    # 解析 AI 生成的信息
    structured_data = {}
    for line in response.text.split('\n'):
        if '：' in line:
            key, value = line.split('：', 1)
            structured_data[key.strip()] = value.strip()
    # 确保所有字段都存在
    required_fields = ['patient_name', 'examination_date', 'sex', 'age', 'refby', 'uhidno', 'examination_type', 'examined_area', 'device_model', 'imaging_findings', 'diagnosis_summary', 'Comment']
    for field in required_fields:
        if field not in structured_data:
            structured_data[field] = ''
    return structured_data

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/<path:filename>')
def static_files(filename):
    return app.send_static_file(filename)

@app.route('/process', methods=['POST'])
def process_file():
    # 处理文件上传逻辑
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
        report_path = generate_report(structured_data, report_id)
        
        return jsonify({'reportId': report_id}), 200
    except Exception as e:
        logging.error(f'Error processing file: {str(e)}')
        return jsonify({'error': f'Error processing file: {str(e)}'}), 500

if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True) 