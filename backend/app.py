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

# -------------- 新增：引入 transformers，用于调用 Llama2 --------------
from transformers import pipeline

# -------------- 1. 获取项目根目录的绝对路径 --------------
# 假设 app.py 位于 backend 目录内，则:
# Path(__file__) => backend/app.py
# Path(__file__).parent => backend/
# Path(__file__).parent.parent => TESTGEN/
BASE_DIR = Path(__file__).parent.parent.absolute()

# -------------- 2. 加载环境变量 (.env) --------------
# .env 文件放在 TESTGEN/ 下，因此用 BASE_DIR / ".env"
load_dotenv(BASE_DIR / ".env")

# --------------------------------------------------
# -------------- 3. 配置 Flask 的静态目录和模板目录 --------------
# static_folder 指向 TESTGEN/static
# template_folder 指向 TESTGEN/template
# --------------------------------------------------
app = Flask(
    __name__,
    static_folder=str(BASE_DIR / 'static'),
    template_folder=str(BASE_DIR / 'template')
)
CORS(app)

# -------------- 4. 配置参数：上传目录等 --------------
UPLOAD_FOLDER = 'uploads'  # 注意这里是相对路径，会在 TESTGEN/ 下创建/使用 uploads/
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# -------------- 5. 在全局范围内初始化 Vosk 语音识别模型 --------------
# model/ 下存放英/中两个模型
vosk_models = {
    'en': Model('model/vosk-model-small-en-us-0.15'),
    'cn': Model('model/vosk-model-small-cn-0.22')
}

# --------------------------------------------------
# -------------- 6. 初始化 Llama2 模型 --------------
# 使用 Hugging Face transformers pipeline 方式
# 注意：加载 Llama2 模型需要较大资源，建议在 GPU 上运行
# --------------------------------------------------
try:
    llama2_generator = pipeline("text-generation", model="gpt2")
except Exception as e:
    logging.error("Llama2 初始化失败: " + str(e))
    llama2_generator = None

# -------------- 7. 配置日志 --------------
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.FileHandler('app.log'),   # 日志输出到文件
        logging.StreamHandler()           # 日志输出到控制台
    ]
)

# -------------------- 路由定义部分 --------------------

# -------------- 首页：返回 template/index.html --------------
@app.route('/')
def index():
    # 访问 http://localhost:5000/ 时，返回 TESTGEN/template/index.html
    return send_from_directory(app.template_folder, 'index.html')

# -------------- 文本上传页面：返回 text-upload.html --------------
@app.route('/text-upload')
def text_upload():
    # 访问 http://localhost:5000/text-upload 时，返回 TESTGEN/template/text-upload.html
    return send_from_directory(app.template_folder, 'text-upload.html')

# -------------- 音频上传页面：返回 audio-upload.html --------------
@app.route('/audio-upload')
def audio_upload():
    # 访问 http://localhost:5000/audio-upload 时，返回 TESTGEN/template/audio-upload.html
    return send_from_directory(app.template_folder, 'audio-upload.html')

# -------------- 静态文件 (CSS/JS/图片等) --------------
# Flask 会自动通过 /static 路由提供 TESTGEN/static 下的文件
# 因此 HTML 中可用 <link rel="stylesheet" href="/static/css/styles.css"> 等方式加载

# -------------------- 业务逻辑函数部分 --------------------

def convert_audio(filepath):
    """将音频文件转换为 Vosk 支持的格式: 单声道 16kHz 16-bit PCM"""
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
    """使用 Tesseract OCR 处理图片，并返回识别到的文本"""
    try:
        img = Image.open(filepath)
        text = pytesseract.image_to_string(img, lang='chi_sim')  # 使用简体中文识别
        return text.strip() or "未识别到文字"
    except Exception as e:
        logging.error(f"图片处理失败: {str(e)}")
        return ""

def process_audio(filepath, language='en'):
    """使用 Vosk 处理音频，根据 language 参数选择英文或中文模型"""
    try:
        filepath = convert_audio(filepath)  # 先转换为 WAV 格式
        model = vosk_models.get(language, vosk_models['en'])  # 默认英文模型
        
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
    """处理纯文本文件，读取并返回内容"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logging.error(f"文本处理失败: {str(e)}")
        return ""

def process_pdf(filepath):
    """使用 pdfminer 处理 PDF 文件，并返回提取的文本"""
    try:
        from pdfminer.high_level import extract_text
        return extract_text(filepath)
    except Exception as e:
        logging.error(f"PDF处理失败: {str(e)}")
        return ""

def process_docx(filepath):
    """使用 python-docx 处理 Word 文档，并返回所有段落文本"""
    try:
        from docx import Document as DocxDocument
        doc = DocxDocument(filepath)
        return '\n'.join([para.text for para in doc.paragraphs])
    except Exception as e:
        logging.error(f"Word处理失败: {str(e)}")
        return ""

def generate_report(data, format='docx', report_id=None):
    """
    使用 template1.docx 模板生成报告文件（或 PDF）。
    data: AI 生成的结构化数据
    format: 'docx' 或 'pdf'
    report_id: 用于区分报告文件名
    """
    try:
        if format == 'docx':
            # 使用 TESTGEN/backend/templates/template1.docx 作为模板
            doc = Document('backend/templates/template1.docx')
            for paragraph in doc.paragraphs:
                for key, value in data.items():
                    placeholder = f"{{{key}}}"
                    paragraph.text = paragraph.text.replace(placeholder, str(value))
            
            # 保存到 TESTGEN/reports/ 下
            report_path = f'reports/{report_id}.docx' if report_id else 'clinical_report.docx'
            doc.save(report_path)
            return report_path
        
        elif format == 'pdf':
            # 生成简单的 PDF 报告
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
    """
    使用 Llama2 生成结构化报告
    text: OCR 或语音识别等得到的文本
    """
    try:
        if llama2_generator is None:
            raise ValueError("Llama2 生成器未初始化")
        
        # 构造提示 Prompt，告知需要哪些字段
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
        
        # 调用 Llama2 生成
        response = llama2_generator(prompt, max_length=512, do_sample=True, temperature=0.7)
        generated_text = response[0]['generated_text']
        
        # 尝试将生成的文本解析为 JSON
        try:
            return json.loads(generated_text)
        except json.JSONDecodeError:
            # 如果无法解析为 JSON，就返回原始字符串
            return {'raw_response': generated_text}
        
    except Exception as e:
        logging.error(f"Llama2生成报告失败: {str(e)}")
        # 如果 AI 生成失败，则返回默认结构
        return {
            'patient_name': '未知',
            'examination_date': '未知',
            'sex': '未知',
            'age': '未知',
            'diagnosis': '无法生成诊断结果',
            'recommendations': ['Llama2服务不可用'],
            'notes': 'AI服务不可用'
        }

# -------------------- 文件上传处理与报告生成 --------------------

@app.route('/process', methods=['POST'])
def process_file():
    """
    处理上传的文件，根据文件类型进行 OCR / 语音识别 / 文本读取 / PDF 提取等操作，
    然后调用 AI 生成结构化报告，最后保存报告并返回 JSON 响应。
    """
    try:
        # 1. 检查是否有文件
        if 'file' not in request.files:
            return jsonify({'error': '未上传文件'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '无效文件'}), 400

        # 2. 保存上传的文件到 TESTGEN/uploads/
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # 3. 根据扩展名选择处理函数
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
        
        # 4. 调用 Llama2 AI 生成结构化报告数据
        structured_data = generate_report_with_ai(text)
        if not structured_data:
            return jsonify({'error': 'AI生成报告失败'}), 500
        
        # 5. 生成报告文件并存储到 TESTGEN/reports/
        report_id = str(uuid.uuid4())
        os.makedirs('reports', exist_ok=True)
        report_path = generate_report(structured_data, 'docx', report_id)
        
        # 6. 返回报告 ID、下载链接和生成的结构化数据
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
    """
    根据 report_id 从 TESTGEN/reports/ 下找到对应的 docx 报告文件并返回给客户端下载
    """
    try:
        report_path = os.path.join('reports', f'{report_id}.docx')
        if not os.path.exists(report_path):
            return jsonify({'error': '报告不存在'}), 404
        return send_file(report_path, as_attachment=True)
    except Exception as e:
        logging.error(f'下载报告失败: {str(e)}')
        return jsonify({'error': f'下载报告失败: {str(e)}'}), 500

# -------------------- 404 错误处理 --------------------

@app.errorhandler(404)
def page_not_found(e):
    """
    当访问的路由或文件不存在时，返回 TESTGEN/template/404.html
    """
    return send_from_directory(app.template_folder, '404.html'), 404

# -------------------- 主函数启动 --------------------

if __name__ == '__main__':
    # 1. 检查必要文件 (index.html / text-upload.html / audio-upload.html / 404.html) 是否存在
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
    
    # 2. 创建必要目录：uploads/ 和 reports/
    Path('uploads').mkdir(exist_ok=True)
    Path('reports').mkdir(exist_ok=True)
    
    # 3. 启动 Flask 服务器，监听 0.0.0.0:5000
    app.run(host='0.0.0.0', port=5000, debug=True)