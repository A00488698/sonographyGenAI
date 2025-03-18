document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.querySelector('.drop-zone');
    const fileInput = document.getElementById('textFileInput');
    const fileNameDisplay = document.getElementById('file-name');
    const textUploadForm = document.getElementById('textUploadForm');

    if (!textUploadForm) {
        console.error('textUploadForm element not found');
        return;
    }

    // Handle drag events
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });

    ['dragleave', 'dragend'].forEach(type => {
        dropZone.addEventListener(type, () => {
            dropZone.classList.remove('dragover');
        });
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        
        if (e.dataTransfer.files.length) {
            fileInput.files = e.dataTransfer.files;
            const fileName = fileInput.files[0] ? fileInput.files[0].name : 'No file selected';
            fileNameDisplay.textContent = `Selected file: ${fileName}`;
        }
    });

    // Handle file selection
    fileInput.addEventListener('change', function() {
        const fileName = this.files[0] ? this.files[0].name : 'No file selected';
        fileNameDisplay.textContent = `Selected file: ${fileName}`;
    });

    // Handle text file upload
    textUploadForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const file = document.getElementById('textFileInput').files[0];
        if (!file) {
            alert('Please select a file first');
            return;
        }

        const formData = new FormData();
        formData.append('file', file);
        formData.append('type', 'text'); // Default file type is text

        const progressContainer = document.getElementById('progressContainer');
        const progressBar = document.getElementById('progressBar');
        progressContainer.style.display = 'block'; // Show progress bar
        progressBar.style.width = '0%';

        try {
            const response = await fetch('http://localhost:5000/process', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }

            const data = await response.json();
            const reportId = data.reportId;

            // Show success message
            document.getElementById('status').innerText = 'Generation successful';

            // Add download functionality
            const downloadLinks = document.getElementById('download-links');
            downloadLinks.innerHTML = `
                <a href="http://localhost:5000/download/${reportId}?format=docx" download>Download DOCX file</a>
                <a href="http://localhost:5000/download/${reportId}?format=pdf" download>Download PDF file</a>
            `;
        } catch (error) {
            console.error('Error:', error);
            document.getElementById('status').innerText = `Generation failed: ${error.message}`;
        } finally {
            progressContainer.style.display = 'none'; // Hide progress bar
        }
    });
});

async function downloadReport(reportId, format) {
    try {
        const response = await fetch(`http://localhost:5000/download/${reportId}?format=${format}`);
        if (!response.ok) {
            throw new Error('File download failed');
        }
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const fileName = response.headers.get('Content-Disposition').split('filename=')[1];
        const a = document.createElement('a');
        a.href = url;
        a.download = fileName;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
    } catch (error) {
        alert('Download failed: ' + error.message);
    }
} 