document.getElementById('upload-form').addEventListener('submit', async function (e) {
    e.preventDefault();
    const fileInput = document.getElementById('file');
    const fileType = document.getElementById('file-type').value;
    const format = document.getElementById('format').value;
    const file = fileInput.files[0];
    const formData = new FormData();
    formData.append('file', file);
    formData.append('type', fileType);
    formData.append('format', format);

    try {
        const response = await fetch('http://localhost:5000/process', {
            method: 'POST',
            body: formData
        });
        if (!response.ok) {
            throw new Error('文件处理失败');
        }
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const fileName = response.headers.get('Content-Disposition').split('filename=')[1];

        // 显示生成成功
        document.getElementById('status').innerText = '生成成功';

        // 添加查看和下载功能
        const downloadLinks = document.getElementById('download-links');
        downloadLinks.innerHTML = `
            <a href="${url}" target="_blank">查看文件</a>
            <a href="${url}" download="${fileName}">下载 ${format.toUpperCase()} 文件</a>
        `;
    } catch (error) {
        document.getElementById('status').innerText = '生成失败: ' + error.message;
    }
}); 