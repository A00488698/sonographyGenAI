import os
import uuid
from pathlib import Path
from docxtpl import DocxTemplate
from datetime import datetime
import logging
from flask import send_file, jsonify, request
import json
import ast
import re

# Get absolute path of project root directory
BASE_DIR = Path(__file__).parent.parent.absolute()

def format_findings(findings):
    """
    将 imaging_findings 格式化为整洁文本
    """
    # 如果是字典，按原逻辑处理
    if isinstance(findings, dict):
        lines = []
        for organ, info in findings.items():
            if info is None:
                continue
            if isinstance(info, dict):
                sub_lines = []
                for key, value in info.items():
                    if value is None:
                        continue
                    if isinstance(value, bool):
                        value = "Yes" if value else "No"
                    elif isinstance(value, list):
                        value = ", ".join([str(v) for v in value if v])
                    sub_lines.append(f"{key.capitalize()}: {value}")
                if sub_lines:
                    lines.append(f"{organ.capitalize()}:\n  " + "\n  ".join(sub_lines))
            else:
                lines.append(f"{organ.capitalize()}: {info}")
        return "\n".join(lines)
    # 如果是列表，尝试对每个元素格式化，如果元素是字典，则格式化为 key: value 格式
    elif isinstance(findings, list):
        lines = []
        for item in findings:
            if isinstance(item, dict):
                sub_lines = []
                for key, value in item.items():
                    if value is None:
                        continue
                    sub_lines.append(f"{key.capitalize()}: {value}")
                lines.append(", ".join(sub_lines))
            else:
                lines.append(str(item))
        return ", ".join(lines)
    else:
        return str(findings)

def format_text_field(field):
    """
    将字段处理为纯文本，不带多余的符号。
    如果字段是列表，则将其拼接为一句话。
    """
    if isinstance(field, list):
        return ", ".join([str(item) for item in field if item])
    return str(field)

def prepare_data_for_template(data):
    if 'imaging_findings' in data:
        data['imaging_findings'] = format_findings(data['imaging_findings'])
    if 'diagnosis_summary' in data:
        data['diagnosis_summary'] = format_text_field(data['diagnosis_summary'])
    if 'comment' in data:
        data['comment'] = format_text_field(data['comment'])
    for key, value in data.items():
        if isinstance(value, str):
            data[key] = value.strip()
    return data

def generate_report(data, format='docx', report_id=None, original_filename=None):
    """
    Generate report file using template1.docx template.
    """
    try:
        # 如果数据中存在 raw_response，尝试提取有效的 JSON 部分并覆盖 data
        if 'raw_response' in data:
            raw = data['raw_response']
            # 查找换行后紧跟 "{" 的位置
            pos = raw.find('\n{')
            if pos != -1:
                json_str = raw[pos+1:]
            else:
                pos = raw.find('{')
                json_str = raw[pos:]
            print("Extracted JSON string:", json_str)
            try:
                parsed = json.loads(json_str)
                data = parsed  # 直接覆盖原来的 data
            except json.JSONDecodeError as parse_e:
                logging.error(f"Failed to parse raw_response using json: {parse_e}")
                try:
                    parsed = ast.literal_eval(json_str)
                    data = parsed  # 直接覆盖原来的 data
                except Exception as ast_e:
                    logging.error(f"Failed to parse raw_response using ast.literal_eval: {ast_e}")
        
        # Ensure data contains all required keys
        required_keys = [
            'patient_name', 'examination_date', 'sex', 'age', 'refby', 'uhidno',
            'examination_type', 'examined_area', 'device_model', 'imaging_findings',
            'diagnosis_summary', 'comment'
        ]
        for key in required_keys:
            if key not in data or not data[key]:
                data[key] = '123'
        
        # Debug: Print the data being used for report generation
        print("Data being used for report generation:", data)
        
        # 对数据进行预处理
        data = prepare_data_for_template(data)
        
        # Load template document using DocxTemplate
        template_path = os.path.join(str(BASE_DIR / 'backend' / 'templates'), 'template1.docx')
        doc = DocxTemplate(template_path)
        
        # Render template using docxtpl，data 作为上下文
        doc.render(data)
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    if cell.text and '{' in cell.text and '}' in cell.text:
                        try:
                            cell.text = cell.text.format(**data)
                        except KeyError:
                            pass
        
        # 确保 reports 目录存在
        reports_dir = BASE_DIR / 'reports'
        reports_dir.mkdir(exist_ok=True)
        if not report_id:
            report_id = str(uuid.uuid4())
        docx_report_path = os.path.join(str(reports_dir), f"{report_id}.docx")
        pdf_report_path = os.path.join(str(reports_dir), f"{report_id}.pdf")
        
        # 保存 DOCX 文件
        doc.save(docx_report_path)
        
        # 如果需要转换为 PDF，则调用 docx2pdf
        if format == 'pdf':
            try:
                from docx2pdf import convert
                print(f"Converting DOCX: {docx_report_path} to PDF: {pdf_report_path}")
                convert(docx_report_path, pdf_report_path)
                return pdf_report_path
            except Exception as conv_e:
                logging.error(f"Failed to convert DOCX to PDF: {conv_e}")
                return docx_report_path
        else:
            return docx_report_path
        
    except Exception as e:
        logging.error(f"Report generation failed: {e}")
        raise

def download_report(report_id):
    """
    Find corresponding docx or pdf report file in TESTGEN/reports/ based on report_id and return to client for download.
    """
    try:
        fmt = request.args.get('format', 'docx')
        reports_dir = str(BASE_DIR / 'reports')
        file_path = os.path.join(reports_dir, f'{report_id}.{fmt}')
        if not os.path.exists(file_path):
            return jsonify({'error': 'Report does not exist'}), 404
        return send_file(file_path, as_attachment=True)
    except Exception as e:
        logging.error(f'Failed to download report: {str(e)}')
        return jsonify({'error': f'Failed to download report: {str(e)}'}), 500