import os
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
        indexer.index_directory(kb_config["documents_dir"])
    
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
            
        with gr.Tab("设置"):
            create_settings_ui(config, model)

    return app

# 运行应用
if __name__ == "__main__":
    app = create_app()
    app.launch(server_name="0.0.0.0", server_port=7860, share=False)