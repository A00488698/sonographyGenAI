# Clinical Report Generation System

## Overview
The Clinical Report Generation System is a web application that allows users to upload clinical notes or audio files, and automatically generates structured clinical reports in both DOCX and PDF formats. The system utilizes OCR (Optical Character Recognition) for image files, speech recognition for audio files, and AI-powered text processing for generating structured reports.

## Features
- **Text Upload**: Upload clinical notes in various formats (TXT, PDF, DOCX, JPG, JPEG)
- **Audio Upload**: Upload audio files (WAV, MP3) for speech-to-text conversion
- **AI-Powered Report Generation**: Generate structured clinical reports using AI models
- **Multiple Output Formats**: Download generated reports in both DOCX and PDF formats
- **User-Friendly Interface**: Simple and intuitive web interface for easy file upload and report generation

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/clinical-report-generation-system.git
   ```
2. Navigate to the project directory:
   ```bash
   cd clinical-report-generation-system
   ```
3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set up environment variables:
   - Create a `.env` file in the root directory
   - Add necessary environment variables (e.g., API keys, model paths)

## Usage
1. Start the Flask server:
   ```bash
   python backend/app.py
   ```
2. Open your web browser and navigate to `http://localhost:5000`
3. Use the web interface to upload files and generate reports

## Project Structure
```
clinical-report-generation-system/
├── backend/               # Backend code and Flask application
├── static/                # Static files (CSS, JS, images)
├── template/              # HTML templates
├── uploads/               # Uploaded files storage
├── reports/               # Generated reports storage
├── requirements.txt       # Python dependencies
└── README.md              # Project documentation
```

## Dependencies
- Flask
- Flask-CORS
- python-dotenv
- pytesseract
- pydub
- vosk
- pdfminer.six
- python-docx
- docxtpl
- Pillow
- transformers
- torch
- uuid
- Werkzeug
- fpdf2
- SpeechRecognition
- wave

## Contributing
Contributions are welcome! Please follow these steps:
1. Fork the repository
2. Create a new branch (`git checkout -b feature/YourFeatureName`)
3. Commit your changes (`git commit -m 'Add some feature'`)
4. Push to the branch (`git push origin feature/YourFeatureName`)
5. Create a new Pull Request

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 