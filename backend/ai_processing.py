import json
import logging
import ollama
def enhance_text_with_ai(text):
    """
    Use AI to enhance and refine the input text
    text: Original text content
    return: Enhanced text
    """
    try:
        prompt = f"""Please enhance and refine the following medical report text. Requirements:
1. Correct obvious grammar and spelling errors
2. Fill in missing information that can be reasonably inferred
3. Use more professional medical terminology
4. Maintain objectivity and accuracy of medical reporting
5. Preserve the authenticity of original information, avoid over-interpretation

Original text:
{text}

Please return only the enhanced text without any explanations or additional content.
"""
        # Call AI model for text enhancement
        response = ollama.generate(model='gemma3', prompt=prompt)
        enhanced_text = response['response']
        
        print("Enhanced text:", enhanced_text)  # Debug log
        return enhanced_text.strip()
        
    except Exception as e:
        logging.error(f"Text enhancement failed: {str(e)}")
        return text  # Return original text if enhancement fails


def generate_report_with_ai(text):
    """
    Generate structured report using Llama2 via Ollama
    text: Text obtained from OCR or speech recognition
    """
    try:
        print("Text passed to AI model:", text)  # 打印传递给模型的文本
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
- comment

Content:
{text}

Output only a valid JSON object.
"""
        
        # Call Llama2 via Ollama
        response = ollama.generate(model='gemma3', prompt=prompt)
        generated_text = response['response']
        
        # Debug: Print the generated text
        print("Generated text from AI1234:", generated_text)
         # 使用正则表达式提取 JSON 部分
        import re
        match = re.search(r'(\{.*\})', generated_text, re.DOTALL)
        if match:
            json_str = match.group(1)
            print("Extracted JSON string:", json_str)
        else:
            # 如果未找到花括号，则直接使用原文本（可能会失败）
            json_str = generated_text
        # Try to parse generated text as JSON
        try:
            data = json.loads(json_str)
            # Ensure all keys are present and have non-empty values
            required_keys = [
                'patient_name', 'examination_date', 'sex', 'age', 'refby', 'uhidno',
                'examination_type', 'examined_area', 'device_model', 'imaging_findings',
                'diagnosis_summary', 'comment'
            ]
            for key in required_keys:
                if key not in data or not data[key]:
                    data[key] = '456'
            return data
        except json.JSONDecodeError:
            # If cannot parse as JSON, return default structure
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
        
    except Exception as e:
        logging.error(f"gemma3 report generation failed: {str(e)}")
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