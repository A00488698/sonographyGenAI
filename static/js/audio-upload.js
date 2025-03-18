document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.querySelector('.drop-zone');
    const fileInput = document.getElementById('audioFileInput');
    const fileNameDisplay = document.getElementById('file-name');
    const submitBtn = document.querySelector('.submit-btn');
    const resultDisplay = document.getElementById('result');

    // 检查必要的元素是否存在
    if (!dropZone || !fileInput || !fileNameDisplay || !submitBtn || !resultDisplay) {
        console.error("One or more required elements are missing.");
        return;
    }

    // 处理拖拽事件
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

    // 处理文件选择
    fileInput.addEventListener('change', function() {
        const fileName = this.files[0] ? this.files[0].name : 'No file selected';
        fileNameDisplay.textContent = `Selected file: ${fileName}`;
    });

    // 处理上传按钮点击事件
    submitBtn.addEventListener('click', async (e) => {
        e.preventDefault();
        console.log("Upload button clicked");
        
        const file = fileInput.files[0];
        if (!file) {
            alert("Please select a file first");
            return;
        }

        const formData = new FormData();
        formData.append('file', file);
        formData.append('type', 'audio');

        try {
            console.log("Sending file to server...");
            const response = await fetch('/process', {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                console.log("File processed successfully");
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'clinical_report.docx';
                document.body.appendChild(a);
                a.click();
                a.remove();
            } else {
                console.error("File processing failed:", response.statusText);
                resultDisplay.innerText = 'File processing failed';
            }
        } catch (error) {
            console.error("Error:", error);
            resultDisplay.innerText = 'An error occurred during processing';
        }
    });
});