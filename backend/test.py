import os
import google.generativeai as genai
from dotenv import load_dotenv
from pathlib import Path

genai.configure(api_key="AIzaSyBZJJNl9yAycmVc141ZUc0YHqS84eVoAlc")
print(genai.GenerativeModel('gemini-1.5-pro').generate_content("你好").text)

