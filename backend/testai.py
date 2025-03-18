import ollama
import json
import logging

def generate_report_with_ai():

    try:
        # Construct prompt, specifying required fields
        prompt = f""" descripe today's weather"""
        
        # Call Llama2 via Ollama
        response = ollama.generate(model='llama2', prompt=prompt)
        generated_text = response['response']
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
        return {"""I dont know"""
            
        }
    
if __name__ == "__main__":
    generate_report_with_ai()