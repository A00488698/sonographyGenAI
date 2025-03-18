# Clinical Report Generation System

This is a web application for generating clinical reports from text or audio files. The system supports multiple file formats and uses AI (Llama2 via Ollama) to process and generate structured reports.

## Features

- **Text Upload**: Upload clinical notes in `.txt`, `.docx`, or `.pdf` format.
- **Audio Upload**: Upload audio files in `.wav` or `.mp3` format for transcription and report generation.
- **Report Generation**: Generate clinical reports in `.docx` or `.pdf` format.
- **AI Integration**: Uses Llama2 via Ollama to process and structure the input data.

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Pip (Python package manager)
- Ollama (for running Llama2 locally)

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

6. Install Ollama and Llama2:
   - Follow the [Ollama installation guide](https://ollama.ai/docs) to set up Llama2 locally.

### Running the Application

1. Start the Flask development server:
   ```bash
   python app2.py
   ```

2. Open your browser and navigate to `http://localhost:5000`.

### Using Llama2 with Ollama

#### Step 1: Install Ollama

1. **macOS/Linux**:
   - Run the following command to install Ollama:
     ```bash
     curl -fsSL https://ollama.ai/install.sh | sh
     ```

2. **Windows**:
   - Download the Ollama installer from the [official website](https://ollama.ai/download).
   - Run the installer and follow the on-screen instructions.

#### Step 2: Download and Run Llama2

1. Download the Llama2 model:
   ```bash
   ollama pull llama2
   ```

2. Run the Llama2 model:
   ```bash
   ollama run llama2
   ```

3. Test the model:
   - After running the model, you can interact with it directly in the terminal. For example:
     ```bash
     >>> What is the capital of France?
     Paris
     ```

#### Step 3: Integrate Llama2 with the Application

The application is already configured to use Llama2 via Ollama. Ensure that Ollama is running in the background when using the application.

### File Structure

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
- ollama
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