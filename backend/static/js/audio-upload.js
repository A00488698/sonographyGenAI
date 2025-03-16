const dropZone = document.querySelector('.drop-zone');
const fileInput = document.getElementById('audioFileInput');

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
        const fileName = fileInput.files[0] ? fileInput.files[0].name : '未选择文件';
        document.getElementById('file-name').textContent = `已选择文件：${fileName}`;
    }
});

// 处理文件选择
fileInput.addEventListener('change', function() {
    const fileName = this.files[0] ? this.files[0].name : '未选择文件';
    document.getElementById('file-name').textContent = `已选择文件：${fileName}`;
});

// 处理音频文件上传
document.getElementById('audioUploadForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const file = document.getElementById('audioFileInput').files[0];
    if (!file) {
        alert('请先选择文件');
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
            document.getElementById('result').innerText = '文件处理失败';
        }
    } catch (error) {
        console.error('Error:', error);
        document.getElementById('result').innerText = '处理过程中发生错误';
    }
}); 