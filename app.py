import os
import sys

# 设置项目根目录和便携式Python环境路径
project_root = os.path.dirname(__file__)
runtime_path = os.path.join(project_root, 'Runtime')

# 将项目根目录添加到sys.path
sys.path.insert(0, project_root)
sys.path.insert(0, runtime_path)
os.environ['PATH'] = runtime_path + os.pathsep + os.environ['PATH']

import yaml
import gradio as gr
from models import create_model
from rag.vectorstore import VectorStore
from rag.indexer import DocumentIndexer
from tree_kb.tree_builder import KnowledgeTreeBuilder
from ui.chat import create_chat_ui
from ui.kb_manager import create_kb_manager_ui
from ui.settings import create_settings_ui

# 加载配置
def load_config():
    with open("config.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

config = load_config()

# 初始化模型
def init_model():
    model_config = config["model"]
    return create_model(
        provider=model_config["provider"],
        model_name=model_config["name"],
        api_key=model_config.get("api_key", ""),
        api_base=model_config.get("api_base", ""),
        temperature=model_config.get("temperature", 0.7)
    )

def load_model():
    """加载模型"""
    try:
        # 读取配置
        with open("config.yaml", "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        model_config = config.get("model", {})

        # 打印模型配置
        print("模型配置:")
        print(f"- 提供者: {model_config.get('provider', 'N/A')}")
        print(f"- 模型名称: {model_config.get('name', 'N/A')}")
        print(f"- API基础URL: {model_config.get('api_base', 'N/A')}")
        print(f"- API密钥设置: {'是' if model_config.get('api_key') else '否'}")

        # 从配置创建模型
        model = create_model(
            provider=model_config.get("provider", ""),
            model_name=model_config.get("name", ""),
            api_key=model_config.get("api_key", ""),
            api_base=model_config.get("api_base", ""),
            temperature=float(model_config.get("temperature", 0.7))
        )

        return model
    except Exception as e:
        print(f"加载模型失败: {e}")
        raise e

# 初始化知识库
def init_knowledge_base():
    kb_config = config["knowledge_base"]
    vector_store = VectorStore(
        embedding_model=kb_config["embedding_model"],
        vector_dir=kb_config["vector_dir"]
    )
    indexer = DocumentIndexer(vector_store)
    
    # 如果配置为自动索引，则索引文档目录
    if kb_config.get("auto_index", False):
        # 使用增量索引
        incremental = kb_config.get("incremental_index", True)
        indexer.index_directory(kb_config["documents_dir"], incremental=incremental)
    
    # 初始化树状知识库
    tree_builder = KnowledgeTreeBuilder(
        documents_dir=kb_config["documents_dir"],
        tree_index_path=kb_config["tree_index_path"]
    )
    
    if kb_config.get("auto_build_tree", False):
        tree_builder.build_tree()
        
    return {
        "vector_store": vector_store,
        "indexer": indexer,
        "tree_builder": tree_builder
    }

# 创建Gradio应用
def create_app():
    # 初始化模型和知识库
    model = init_model()
    kb = init_knowledge_base()
    
    # 创建Gradio界面
    with gr.Blocks(theme=gr.themes.Soft(), title="AI助手") as app:
        with gr.Tab("对话"):
            create_chat_ui(model, kb)
        
        with gr.Tab("知识库管理"):
            create_kb_manager_ui(kb)
            
        with gr.Tab("设置 (记得要“保存配置”)"):
            create_settings_ui(config, model)

    return app

# 运行应用
if __name__ == "__main__":
    app = create_app()
    app.launch(server_name="127.0.0.1", server_port=7860, share=False)