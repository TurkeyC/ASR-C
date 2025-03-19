# ASR-C

这是一个基于Gradio的WebUI项目，用于实现与AI大模型的多轮对话，并支持RAG和树状结构的知识库功能。

## 功能特点

- 支持多种AI大模型
  - OpenAI API
  - 本地Ollama
  - LMStudio本地模型
- 基于RAG的知识库检索
- 树状结构知识库导航
- 简洁直观的Web用户界面
- 支持Markdown文档的自动索引

## 快速开始

### 1. 安装依赖

```bash
# 创建虚拟环境(可选)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 安装依赖包
pip install -r requirements.txt
```

### 2. 配置

编辑`config.yaml`文件，设置您的AI模型提供商、API密钥等信息