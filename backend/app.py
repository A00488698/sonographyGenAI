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
import google.generativeai as genai
from dotenv import load_dotenv

# 获取项目根目录的绝对路径
BASE_DIR = Path(__file__).parent.parent.absolute()

# 加载环境变量
load_dotenv(BASE_DIR / ".env")  # ✅ 明确指定路径

# --------------------------------------------------
# 关键：修正 Flask 的静态目录和模板目录
# --------------------------------------------------
# 假设你在 backend/static 下放置了 css/ js/ 等静态文件
# 并且在项目根目录下的 template 文件夹里放了 index.html、404.html 等页面
app = Flask(
    __name__,
    static_folder=str(BASE_DIR / 'backend' / 'static'),   # 指向 backend/static
    template_folder=str(BASE_DIR / 'template')            # 指向 template
)
CORS(app)

# 配置参数
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 在全局范围内初始化模型
vosk_models = {
    'en': Model('model/vosk-model-small-en-us-0.15'),
    'cn': Model('model/vosk-model-small-cn-0.22')
}

# 初始化Google AI
genai.configure(api_key="AIzaSyBZJJNl9yAycmVc141ZUc0YHqS84eVoAlc")
print(genai.GenerativeModel('gemini-1.5-pro').generate_content("测试链接").text)

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

@app.route('/')
def index():
    # 访问根路径时，直接从 template_folder 返回 index.html
    return send_from_directory(app.template_folder, 'index.html')

@app.route('/<path:filename>')
@app.route('/static/<path:filename>')
def static_proxy(filename):
    """
    1. 优先匹配静态资源（backend/static）
    2. 再匹配 template 文件夹（template/index.html 等）
    3. 再匹配报告下载
    4. 最后返回 404
    """
    # 优先匹配静态资源
    static_path = Path(app.static_folder) / filename
    if static_path.exists():
        return send_from_directory(app.static_folder, filename)
    
    # 匹配模板文件
    template_path = Path(app.template_folder) / filename
    if template_path.exists():
        return send_from_directory(app.template_folder, filename)
    
    # 匹配报告下载
    if filename.startswith('download/'):
        report_id = filename.split('/')[-1]
        return send_file(f'reports/{report_id}.docx', as_attachment=True)
    
    # 返回404页面
    return send_from_directory(app.template_folder, '404.html'), 404

def convert_audio(filepath):
    """将音频文件转换为 Vosk 支持的格式"""
    try:
        audio = AudioSegment.from_file(filepath)
        audio = audio.set_channels(1).set_frame_rate(16000).set_sample_width(2)
        converted_path = Path(filepath).with_suffix('.wav')
        audio.export(converted_path, format="wav")
        return str(converted_path)
    except Exception as e:
        logging.error(f"音频转换失败: {str(e)}")
        raise

def process_image(filepath):
    """使用Tesseract OCR处理图片"""
    try:
        img = Image.open(filepath)
        text = pytesseract.image_to_string(img, lang='chi_sim')
        return text.strip() or "未识别到文字"
    except Exception as e:
        logging.error(f"图片处理失败: {str(e)}")
        return ""

def process_audio(filepath, language='en'):
    """使用Vosk处理音频"""
    try:
        filepath = convert_audio(filepath)
        model = vosk_models.get(language, vosk_models['en'])
        
        wf = wave.open(filepath, "rb")
        if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getframerate() not in [8000, 16000]:
            raise ValueError("音频格式不支持，需要单声道16-bit PCM WAV格式，采样率8000或16000Hz")
        
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
        logging.error(f"音频处理失败: {str(e)}")
        return ""

def process_text(filepath):
    """处理文本文件"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logging.error(f"文本处理失败: {str(e)}")
        return ""

def process_pdf(filepath):
    """处理PDF文件"""
    try:
        from pdfminer.high_level import extract_text
        return extract_text(filepath)
    except Exception as e:
        logging.error(f"PDF处理失败: {str(e)}")
        return ""

def process_docx(filepath):
    """处理Word文档"""
    try:
        from docx import Document as DocxDocument
        doc = DocxDocument(filepath)
        return '\n'.join([para.text for para in doc.paragraphs])
    except Exception as e:
        logging.error(f"Word处理失败: {str(e)}")
        return ""

def generate_report(data, format='docx', report_id=None):
    """生成报告"""
    try:
        if format == 'docx':
            doc = Document('backend/templates/template1.docx')
            for paragraph in doc.paragraphs:
                for key, value in data.items():
                    placeholder = f"{{{key}}}"
                    paragraph.text = paragraph.text.replace(placeholder, str(value))
            
            report_path = f'reports/{report_id}.docx' if report_id else 'clinical_report.docx'
            doc.save(report_path)
            return report_path
        
        elif format == 'pdf':
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            for key, value in data.items():
                pdf.cell(200, 10, txt=f"{key}: {value}", ln=True)
            
            report_path = f'reports/{report_id}.pdf' if report_id else 'clinical_report.pdf'
            pdf.output(report_path)
            return report_path
        
    except Exception as e:
        logging.error(f"报告生成失败: {str(e)}")
        raise

def generate_report_with_ai(text):
    """使用Google AI生成结构化报告"""
    try:
        model = genai.GenerativeModel('gemini-1.5-pro')
        prompt = f"""请根据以下内容生成结构化报告：
        {text}
        
        报告应包括以下字段：
        - 患者姓名 (patient_name)
        - 检查日期 (examination_date)
        - 性别 (sex)
        - 年龄 (age)
        - 诊断结果 (diagnosis)
        - 建议 (recommendations)
        - 备注 (notes)"""
        
        response = model.generate_content(prompt)
        
        if not response or not response.text:
            raise ValueError("Invalid response from Google AI")
            
        # 尝试解析为JSON
        try:
            return json.loads(response.text)
        except json.JSONDecodeError:
            return {'raw_response': response.text}
        
    except Exception as e:
        logging.error(f"AI生成报告失败: {str(e)}")
        return {
            'patient_name': '未知',
            'examination_date': '未知',
            'sex': '未知',
            'age': '未知',
            'diagnosis': '无法生成诊断结果',
            'recommendations': ['请检查API密钥'],
            'notes': 'AI服务不可用'
        }

@app.route('/process', methods=['POST'])
def process_file():
    try:
        if 'file' not in request.files:
            return jsonify({'error': '未上传文件'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '无效文件'}), 400

        # 保存文件
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # 根据文件类型处理
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
            return jsonify({'error': '不支持的文件类型'}), 400
        
        text = processors[ext](filepath)
        
        # 使用AI生成报告
        structured_data = generate_report_with_ai(text)
        if not structured_data:
            return jsonify({'error': 'AI生成报告失败'}), 500
        
        # 生成报告文件
        report_id = str(uuid.uuid4())
        os.makedirs('reports', exist_ok=True)
        report_path = generate_report(structured_data, 'docx', report_id)
        
        return jsonify({
            'reportId': report_id,
            'downloadUrl': f'/download/{report_id}',
            'data': structured_data
        }), 200
        
    except Exception as e:
        logging.error(f"处理失败: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/download/<report_id>', methods=['GET'])
def download_report(report_id):
    try:
        report_path = os.path.join('reports', f'{report_id}.docx')
        
        if not os.path.exists(report_path):
            return jsonify({'error': '报告不存在'}), 404
            
        return send_file(report_path, as_attachment=True)
    except Exception as e:
        logging.error(f'下载报告失败: {str(e)}')
        return jsonify({'error': f'下载报告失败: {str(e)}'}), 500

@app.errorhandler(404)
def page_not_found(e):
    return send_from_directory(app.template_folder, '404.html'), 404

if __name__ == '__main__':
    # 检查必要文件
    required_files = [
        BASE_DIR / 'template' / 'index.html',
        BASE_DIR / 'template' / 'text-upload.html',
        BASE_DIR / 'template' / 'audio-upload.html',
        BASE_DIR / 'template' / '404.html'
    ]
    
    for file_path in required_files:
        if not file_path.exists():
            logging.critical(f"关键文件缺失: {file_path}")
            exit(1)
    
    for file_path in required_files:
        if not file_path.exists():
            logging.critical(f"关键文件缺失: {file_path}")
            exit(1)
    
    # 创建必要目录
    Path('uploads').mkdir(exist_ok=True)
    Path('reports').mkdir(exist_ok=True)
    
    app.run(host='0.0.0.0', port=5000, debug=True)