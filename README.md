# Your Reliable Report Assistant

Your Reliable Report Assistant is a web application for generating clinical reports from text or audio files. The system supports multiple file formats and uses AI (gemma3 via Ollama) to process and generate structured reports.

## Features

- **Text Upload**: Upload report notes in `.txt`, `.docx`, or `.pdf` format.
- **Audio Upload**: Upload audio files in `.wav` or `.mp3` format for transcription and report generation.
- **Report Generation**: Generate structured reports in `.docx` or `.pdf` format.
- **AI Integration**: Uses gemma3 via Ollama to process and structure the input data.
- **File Card Display**: Uploaded files are displayed as cards with delete and progress bar functionality.
- **Audio-to-Text Transcription**: Uses Whisper for high-accuracy audio-to-text transcription.


## Getting Started

### Prerequisites

- Python 3.8 or higher
- Pip (Python package manager)
- Ollama (for running gemma3 locally)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/A00488698/sonographyGenAI.git
   cd sonographyGenAI
   cd backend
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

6. Install Ollama and gemma3:
   - Follow the [Ollama installation guide](https://ollama.ai/docs) to set up gemma3 locally.

### Running the Application

1. Start the Flask development server:
   ```bash
   python app2.py
   ```

2. Open your browser and navigate to `http://localhost:5000`.