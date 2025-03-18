# Clinical Report Generation System

This is a web application for generating clinical reports from text or audio files. The system supports multiple file formats and uses AI to process and generate structured reports.

## Features

- **Text Upload**: Upload clinical notes in `.txt`, `.docx`, or `.pdf` format.
- **Audio Upload**: Upload audio files in `.wav` or `.mp3` format for transcription and report generation.
- **Report Generation**: Generate clinical reports in `.docx` or `.pdf` format.
- **AI Integration**: Uses AI to process and structure the input data.

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Pip (Python package manager)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-repo/clinical-report-generation.git
   cd clinical-report-generation
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   ```

3. Activate the virtual environment:
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Set up environment variables:
   - Create a `.env` file in the root directory.
   - Add necessary environment variables (e.g., API keys, paths).

### Running the Application

1. Start the Flask development server:
   ```bash
   python app2.py
   ```

2. Open your browser and navigate to `http://localhost:5000`.

### File Structure
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

1. Fork the repository.
2. Create a new branch (`git checkout -b feature/YourFeature`).
3. Commit your changes (`git commit -m 'Add some feature'`).
4. Push to the branch (`git push origin feature/YourFeature`).
5. Open a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details. 