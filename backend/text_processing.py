import os
from pathlib import Path
from PIL import Image
import pytesseract
from pydub import AudioSegment
import wave
import json
import logging
import whisper  # 导入 Whisper

def convert_audio(filepath):
    """Convert audio file to Whisper supported format: mono 16kHz 16-bit PCM"""
    try:
        audio = AudioSegment.from_file(filepath)
        audio = audio.set_channels(1).set_frame_rate(16000).set_sample_width(2)
        converted_path = Path(filepath).with_suffix('.wav')
        audio.export(converted_path, format="wav")
        print(f"Audio converted and saved to: {converted_path}")  # 打印转换后的文件路径
        return str(converted_path)
    except Exception as e:
        logging.error(f"Audio conversion failed: {str(e)}")
        raise

def process_image(filepath):
    """Process image using Tesseract OCR and return recognized text"""
    try:
        img = Image.open(filepath)
        text = pytesseract.image_to_string(img, lang='eng')
        return text.strip() or "No text recognized"
    except Exception as e:
        logging.error(f"Image processing failed: {str(e)}")
        return ""

def process_audio(filepath, language='en'):
    """Process audio using Whisper and return transcribed text"""
    try:
        # 加载 Whisper 模型
        model = whisper.load_model("base")  # 可以选择 "tiny", "base", "small", "medium", "large"
        
        # 转写音频
        result = model.transcribe(filepath)
        print("Transcribed text:", result["text"])  # 打印转写结果
        return result["text"].strip() or "No speech recognized"
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