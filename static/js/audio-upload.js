document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.querySelector('.drop-zone');
    const fileInput = document.getElementById('audioFileInput');
    const fileList = document.getElementById('fileList');
    const submitBtn = document.querySelector('.submit-btn');
    const resultDisplay = document.getElementById('result');

    // 检查必要的元素是否存在
    if (!dropZone || !fileInput || !fileList || !submitBtn || !resultDisplay) {
        console.error("One or more required elements are missing.");
        return;
    }

    // ==========================
    // 1. 拖拽交互
    // ==========================
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
        if (e.dataTransfer.files && e.dataTransfer.files.length) {
            handleFiles(e.dataTransfer.files);
        }
    });

    // ==========================
    // 2. 文件选择
    // ==========================
    fileInput.addEventListener('change', (e) => {
        if (e.target.files && e.target.files.length) {
            handleFiles(e.target.files);
            // 清空 input，方便再次选择同样文件
            fileInput.value = '';
        }
    });

    // ==========================
    // 3. 处理选中的文件
    // ==========================
    function handleFiles(files) {
        Array.from(files).forEach(file => {
            // 创建一个文件条目的 DOM
            const fileItem = createFileItem(file);
            fileList.appendChild(fileItem);

            // 进行上传
            uploadFile(file, fileItem);
        });
    }

    // ==========================
    // 4. 创建文件条目 DOM
    // ==========================
    function createFileItem(file) {
        // 外容器
        const fileItem = document.createElement('div');
        fileItem.className = 'file-item';

        // 文件图标
        const fileIcon = document.createElement('div');
        fileIcon.className = 'file-icon';
        fileIcon.textContent = getFileExtensionIcon(file.name); // 仅简单显示后缀
        fileItem.appendChild(fileIcon);

        // 文件信息
        const fileInfo = document.createElement('div');
        fileInfo.className = 'file-info';

        // 文件名
        const fileName = document.createElement('div');
        fileName.className = 'file-name';
        fileName.textContent = file.name;
        fileInfo.appendChild(fileName);

        // 文件大小 + 剩余时间
        const fileMeta = document.createElement('div');
        fileMeta.className = 'file-meta';
        fileMeta.textContent = `${(file.size / 1024 / 1024).toFixed(2)} MB • 0s left`;
        fileInfo.appendChild(fileMeta);

        // 进度条容器
        const progressBar = document.createElement('div');
        progressBar.className = 'progress-bar';
        // 进度条填充
        const progressFill = document.createElement('div');
        progressFill.className = 'progress-fill';
        progressBar.appendChild(progressFill);

        // 百分比文本
        const progressText = document.createElement('div');
        progressText.className = 'progress-text';
        progressText.textContent = '0%';
        progressBar.appendChild(progressText);

        fileInfo.appendChild(progressBar);

        fileItem.appendChild(fileInfo);

        // 上传完成标记
        const fileDone = document.createElement('div');
        fileDone.className = 'file-done';
        fileDone.textContent = ''; // 初始为空，上传完成后再显示
        fileItem.appendChild(fileDone);

        return fileItem;
    }

    // ==========================
    // 5. 上传文件 + 更新进度
    // ==========================
    function uploadFile(file, fileItem) {
        const progressFill = fileItem.querySelector('.progress-fill');
        const progressText = fileItem.querySelector('.progress-text');
        const fileMeta = fileItem.querySelector('.file-meta');
        const fileDone = fileItem.querySelector('.file-done');

        const formData = new FormData();
        formData.append('file', file);
        formData.append('type', 'audio');

        const xhr = new XMLHttpRequest();

        // 打开请求
        xhr.open('POST', '/process');

        // 监听进度
        xhr.upload.onprogress = function (e) {
            if (e.lengthComputable) {
                const percent = (e.loaded / e.total) * 100;
                progressFill.style.width = percent.toFixed(2) + '%';
                progressText.textContent = percent.toFixed(0) + '%';

                // 简单模拟剩余时间：假设平均 500kB/s
                const speed = 500 * 1024; // 500KB/s
                const bytesLeft = e.total - e.loaded;
                const timeLeft = bytesLeft / speed; // 秒
                if (timeLeft > 0) {
                    fileMeta.textContent = `${(file.size / 1024 / 1024).toFixed(2)} MB • ${Math.ceil(timeLeft)}s left`;
                } else {
                    fileMeta.textContent = `${(file.size / 1024 / 1024).toFixed(2)} MB • finishing...`;
                }
            }
        };

        // 完成时
        xhr.onload = function () {
            if (xhr.status === 200) {
                const data = JSON.parse(xhr.responseText);
                console.log("Server response:", data); // 打印服务器返回的数据

                // 更新进度条和状态
                progressFill.style.width = '100%';
                progressText.textContent = '100%';
                fileMeta.textContent = `${(file.size / 1024 / 1024).toFixed(2)} MB • just now`;
                fileDone.textContent = 'Done';
                fileDone.style.color = '#4caf50';

                // 显示删除按钮（垃圾桶图标）
                const deleteButton = document.createElement('button');
                deleteButton.className = 'delete-btn';
                deleteButton.innerHTML = '<i class="fas fa-trash"></i>'; // 使用 Font Awesome 图标
                deleteButton.onclick = function () {
                    fileItem.remove(); // 删除文件条目
                };
                fileItem.appendChild(deleteButton);

                // 处理生成报告的逻辑
                const reportId = data.reportId;
                resultDisplay.innerHTML = `
                    <p>Report generated successfully!</p>
                    <a href="/download/${reportId}?format=docx" download>Download DOCX</a>
                    <a href="/download/${reportId}?format=pdf" download>Download PDF</a>
                `;
            } else {
                console.error("Upload failed:", xhr.statusText);
                fileDone.textContent = 'Failed';
                fileDone.style.color = '#f44336';
            }
        };

        // 错误时
        xhr.onerror = function () {
            fileDone.textContent = 'Error';
            fileDone.style.color = '#f44336';
        };

        // 发起请求
        xhr.send(formData);
    }

    // ==========================
    // 6. 简单的后缀图标逻辑
    // ==========================
    function getFileExtensionIcon(filename) {
        const ext = filename.split('.').pop().toLowerCase();
        if (ext === 'pdf') return '📄';
        if (ext === 'csv' || ext === 'xls' || ext === 'xlsx') return '📊';
        if (ext === 'doc' || ext === 'docx') return '📝';
        if (ext === 'jpg' || ext === 'png' || ext === 'gif') return '🖼️';
        // 其他类型就统一用一个图标
        return '📁';
    }
});