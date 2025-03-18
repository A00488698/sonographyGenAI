const dropZone = document.querySelector('.drop-zone');
const fileInput = document.getElementById('audioFileInput');

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
        document.getElementById('file-name').textContent = `Selected file: ${fileName}`;
    }
});

// Handle file selection
fileInput.addEventListener('change', function() {
    const fileName = this.files[0] ? this.files[0].name : 'No file selected';
    document.getElementById('file-name').textContent = `Selected file: ${fileName}`;
});

// Handle audio file upload
document.getElementById('audioUploadForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const file = document.getElementById('audioFileInput').files[0];
    if (!file) {
        alert('Please select a file first');
        return;
    }

    const formData = new FormData();
    formData.append('file', file);
    formData.append('type', 'audio');

    try {
        const response = await fetch('/process', {
            method: 'POST',
            body: formData
        });

        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'clinical_report.docx';
            document.body.appendChild(a);
            a.click();
            a.remove();
        } else {
            document.getElementById('result').innerText = 'File processing failed';
        }
    } catch (error) {
        console.error('Error:', error);
        document.getElementById('result').innerText = 'An error occurred during processing';
    }
}); 