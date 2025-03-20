# MarkTreeChat (ASR-C)

这是一个基于Gradio的WebUI项目，用于实现与AI大模型的多轮对话，并支持RAG和树状结构的知识库功能。

## 功能特点

- 支持多种AI大模型
  - OpenAI、Moonshot、Deepseek API
  - 本地Ollama
  - LMStudio本地模型
- 基于RAG的知识库检索
- 树状结构知识库导航
- 简洁直观的Web用户界面
- 支持Markdown文档的自动索引

## 项目的不足与其他开发计划

详情见 [开发日志](Developer_Log.md)

## 项目目录结构

```text
ai-assistant/
├── runtime/               # 嵌入式Python环境
├── app.py                 # 主应用入口
├── config.yaml            # 配置文件
├── requirements.txt       # 依赖包列表
├── models/                # 模型连接器
│   ├── __init__.py
│   ├── base.py            # 模型基类
│   ├── openai_model.py    # OpenAI API连接器
│   ├── ollama_model.py    # Ollama连接器
│   └── lmstudio_model.py  # LMStudio连接器
├── knowledge/             # 知识库
│   ├── documents/         # 存放Markdown文档
│   ├── embeddings/        # 存放文档向量嵌入
│   └── index/             # 存放索引文件
├── rag/                   # RAG相关组件
│   ├── __init__.py
│   ├── vectorstore.py     # 向量数据库操作
│   ├── retriever.py       # 检索器
│   └── indexer.py         # 文档索引器
├── tree_kb/               # 树状结构知识库
│   ├── __init__.py
│   ├── tree_builder.py    # 树状结构构建
│   └── navigator.py       # 树状结构导航
├── ui/                    # UI组件
│   ├── __init__.py
│   ├── chat.py            # 聊天界面
│   ├── kb_manager.py      # 知识库管理界面
│   └── settings.py        # 设置界面
└── utils/                 # 工具函数
    ├── __init__.py
    ├── markdown_parser.py # Markdown解析工具
    └── embedding_utils.py # 嵌入工具
```

## 快速开始

前往 [Releases](https://github.com/TurkeyC/MarkTreeChat/releases/download/v0.1/MarkTreeChat_OneKey_v0.1.zip) 下载最新v0.1版本的一键包，解压后运行`start.bat`即可。

## 手动部署

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
