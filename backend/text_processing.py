import os
from pathlib import Path
from PIL import Image
import pytesseract
from pydub import AudioSegment
import wave
import json
from vosk import Model
import logging

# Initialize Vosk speech recognition models globally
vosk_models = {
    'en': Model('model/vosk-model-small-en-us-0.15'),
    'cn': Model('model/vosk-model-small-cn-0.22')
}

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
        text = pytesseract.image_to_string(img, lang='eng')
        return text.strip() or "No text recognized"
    except Exception as e:
        logging.error(f"Image processing failed: {str(e)}")
        return ""

def process_audio(filepath, language='en'):
    """Process audio using Vosk, select English or Chinese model based on language parameter"""
    try:
        filepath = convert_audio(filepath)
        model = vosk_models.get(language, vosk_models['en'])
        
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