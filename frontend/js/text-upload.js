document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.querySelector('.drop-zone');
    const fileInput = document.getElementById('textFileInput');
    const textUploadForm = document.getElementById('textUploadForm');

    if (!textUploadForm) {
        console.error('textUploadForm 元素未找到');
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
            const fileName = fileInput.files[0] ? fileInput.files[0].name : '未选择文件';
            document.getElementById('file-name').textContent = `已选择文件：${fileName}`;
        }
    });

    // 处理文件选择
    fileInput.addEventListener('change', function() {
        const fileName = this.files[0] ? this.files[0].name : '未选择文件';
        document.getElementById('file-name').textContent = `已选择文件：${fileName}`;
    });

    // 处理文本文件上传
    textUploadForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const file = document.getElementById('textFileInput').files[0];
        if (!file) {
            alert('请先选择文件');
            return;
        }

        const formData = new FormData();
        formData.append('file', file);
        formData.append('type', 'text'); // 默认文件类型为文本

        const progressContainer = document.getElementById('progressContainer');
        const progressBar = document.getElementById('progressBar');
        progressContainer.style.display = 'block'; // 显示进度条
        progressBar.style.width = '0%';

        try {
            const response = await fetch('http://localhost:5000/process', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error('文件处理失败');
            }

            const data = await response.json();
            const reportId = data.reportId;

            // 显示生成成功
            document.getElementById('status').innerText = '生成成功';

            // 添加下载功能
            const downloadLinks = document.getElementById('download-links');
            downloadLinks.innerHTML = `
                <a href="http://localhost:5000/download/${reportId}?format=docx" download>下载 DOCX 文件</a>
                <a href="http://localhost:5000/download/${reportId}?format=pdf" download>下载 PDF 文件</a>
            `;
        } catch (error) {
            console.error('Error:', error);
            document.getElementById('result').innerText = '处理过程中发生错误';
        } finally {
            progressContainer.style.display = 'none'; // 隐藏进度条
        }
    });
});

async function downloadReport(reportId, format) {
    try {
        const response = await fetch(`http://localhost:5000/download/${reportId}?format=${format}`);
        if (!response.ok) {
            throw new Error('文件下载失败');
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
        alert('下载失败: ' + error.message);
    }
} 