import gradio as gr
import time
from typing import Dict, List, Any
from models.base import BaseModel

def create_chat_ui(model: BaseModel, kb: Dict[str, Any]):
    """创建聊天界面"""
    
    # 获取知识库组件
    vector_store = kb["vector_store"]
    retriever = kb["indexer"].retriever
    tree_builder = kb["tree_builder"]
    
    # 全局聊天历史记录
    chat_history = []
    
    # 处理用户消息
    def respond(message, history, system_prompt, use_rag, top_k, temperature):
        # 更新聊天历史
        chat_history.append({"role": "user", "content": message})
        
        try:
            # 准备上下文（如果启用了RAG）
            context = ""
            if use_rag:
                context = retriever.get_retrieval_context(message, top_k=int(top_k))
                if context:
                    # 添加检索上下文到系统提示
                    if system_prompt:
                        system_prompt += "\n\n以下是与用户问题相关的参考信息，请在回答时使用这些信息：\n" + context
                    else:
                        system_prompt = "以下是与用户问题相关的参考信息，请在回答时使用这些信息：\n" + context
            
            # 获取模型回复
            reply = model.chat(
                messages=chat_history,
                system_prompt=system_prompt,
                temperature=float(temperature)
            )
            
            # 更新聊天历史
            chat_history.append({"role": "assistant", "content": reply})
            
            return reply
        except Exception as e:
            return f"发生错误: {str(e)}"
    
    # 创建界面组件
    with gr.Row():
        with gr.Column(scale=3):
            # 主聊天区域
            chatbot = gr.Chatbot(height=600)
            msg = gr.Textbox(placeholder="在此输入您的问题...", lines=3)
            
            with gr.Row():
                submit_btn = gr.Button("发送")
                clear_btn = gr.Button("清除对话")
        
        with gr.Column(scale=1):
            # 设置面板
            with gr.Accordion("对话设置", open=True):
                system_prompt = gr.Textbox(
                    placeholder="输入系统提示词...", 
                    label="系统提示词", 
                    lines=3
                )
                use_rag = gr.Checkbox(label="启用知识库检索", value=True)
                top_k = gr.Slider(
                    minimum=1, 
                    maximum=10, 
                    value=3, 
                    step=1, 
                    label="检索文档数量"
                )
                temperature = gr.Slider(
                    minimum=0.0, 
                    maximum=1.0, 
                    value=0.7, 
                    step=0.1, 
                    label="温度参数"
                )
    
    # 设置事件处理
    submit_btn.click(
        respond,
        inputs=[msg, chatbot, system_prompt, use_rag, top_k, temperature],
        outputs=[chatbot]
    )
    
    msg.submit(
        respond,
        inputs=[msg, chatbot, system_prompt, use_rag, top_k, temperature],
        outputs=[chatbot]
    )
    
    clear_btn.click(
        lambda: [], 
        outputs=[chatbot]
    )