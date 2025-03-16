const express = require('express');
const path = require('path');
const app = express();
const port = 3000;

// 设置静态文件目录
app.use(express.static(path.join(__dirname, 'static')));

// 定义路由
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'templates', 'index.html'));
});

app.get('/text-upload', (req, res) => {
    res.sendFile(path.join(__dirname, 'templates', 'text-upload.html'));
});

app.get('/audio-upload', (req, res) => {
    res.sendFile(path.join(__dirname, 'templates', 'audio-upload.html'));
});

// 处理404错误
app.use((req, res) => {
    res.status(404).sendFile(path.join(__dirname, 'templates', '404.html'));
});

// 启动服务器
app.listen(port, () => {
    console.log(`服务器运行在 http://localhost:${port}`);
}); 