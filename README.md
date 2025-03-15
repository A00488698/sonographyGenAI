# 临床报告生成系统

本项目是一个基于 Web 的临床报告生成系统，支持上传文本、音频和图片文件，通过 AI 技术生成结构化的临床报告，并提供下载功能。

## 功能特性

1. **文件上传**：
   - 支持拖拽上传和点击选择文件。
   - 支持的文件类型：`.txt`、`.pdf`、`.docx`、`.jpg`、`.jpeg`、`.wav`、`.mp3`。

2. **AI 处理**：
   - 使用 Google Gemini API 对上传的文件进行分析，生成结构化的临床报告。

3. **报告生成**：
   - 根据 AI 生成的内容，填充到模板文件中，生成 `.docx` 或 `.pdf` 格式的报告。

4. **下载功能**：
   - 提供下载链接，支持下载生成的报告文件。

5. **进度显示**：
   - 显示文件上传和处理的进度。

## 技术栈

- **前端**：
  - HTML、CSS、JavaScript
  - 使用 `Font Awesome` 图标库
  - 使用 `Fetch API` 进行异步请求

- **后端**：
  - Python、Flask
  - 使用 `Google Gemini API` 进行文件分析
  - 使用 `python-docx` 和 `FPDF` 生成报告

- **文件处理**：
  - 支持文本、音频、图片文件的解析和处理。

## 使用方法

### 1. 安装依赖

确保已安装 Python 3.x，然后安装项目依赖：

```bash
pip install flask python-docx fpdf google-generativeai
```

### 2. 配置 API 密钥

在 `backend/app.py` 中，设置 Google Gemini API 的密钥：

```python
genai.configure(api_key='YOUR_GOOGLE_API_KEY')
```

### 3. 运行项目

启动 Flask 应用：

```bash
python backend/app.py
```

### 4. 访问页面

打开浏览器，访问 `http://localhost:5000`，上传文件并生成报告。

## 项目结构 