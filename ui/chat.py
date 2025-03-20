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
        try:
            # 打印当前模型配置进行调试
            print(f"使用模型: {model.model_name}")
            print(f"API基础URL: {getattr(model, 'api_base', 'N/A')}")
            if hasattr(model, 'api_key') and model.api_key:
                print(f"API密钥前后4位: {model.api_key[:4]}...{model.api_key[-4:] if len(model.api_key) >= 8 else ''}")

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

            # 获取聊天历史
            current_chat_history = []
            if history:
                for entry in history:
                    # 正确映射角色名称
                    user_msg = {"role": "user", "content": entry[0]}
                    assistant_msg = {"role": "assistant", "content": entry[1]}
                    current_chat_history.append(user_msg)
                    current_chat_history.append(assistant_msg)

            # 添加用户最新消息
            current_chat_history.append({"role": "user", "content": message})

            # 添加LaTeX渲染提示到系统提示中
            if system_prompt:
                system_prompt += "\n\n请在回答中使用适当的LaTeX格式展示公式：行内公式使用$符号包围，行间公式使用$$符号包围。"
            else:
                system_prompt = "请在回答中使用适当的LaTeX格式展示公式：行内公式使用$符号包围，行间公式使用$$符号包围。"

            # 获取模型回复
            reply = model.chat(
                messages=current_chat_history,
                system_prompt=system_prompt,
                temperature=float(temperature)
            )

            # 确保reply是字符串
            if not isinstance(reply, str):
                reply = str(reply)

            # 更新聊天历史
            history = history + [(message, reply)]

            # 关键修复：返回空字符串和更新的历史记录
            return "", history
        except Exception as e:
            error_msg = f"发生错误: {str(e)}"
            # 添加错误信息到历史记录
            history = history + [(message, error_msg)]
            return "", history

    # 创建界面组件
    with gr.Row():
        with gr.Column(scale=3):
            # 主聊天区域 - 确保启用Markdown和LaTeX渲染
            chatbot = gr.Chatbot(height=600, render_markdown=True, latex_delimiters=[
                {"left": "$$", "right": "$$", "display": True},
                {"left": "$", "right": "$", "display": False}
            ])

            # 提示用户可以使用LaTeX
            msg = gr.Textbox(
                placeholder="在此输入您的问题...（支持LaTeX公式）",
                lines=3
            )

            with gr.Row():
                submit_btn = gr.Button("发送")
                clear_btn = gr.Button("清除对话")

            # 添加LaTeX使用指南
            latex_guide = """
            ### LaTeX公式支持
            - **行内公式**：使用单个美元符号包围，如 $E=mc^2$
            - **行间公式**：使用双美元符号包围，如 
              $$\\frac{d}{dx}f(x)=\\lim_{h\\to 0}\\frac{f(x+h)-f(x)}{h}$$
            
            您可以在对话中直接使用LaTeX语法，AI助手的回复也会以LaTeX格式展示数学公式。
            """
            gr.Markdown(latex_guide)

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
        outputs=[msg, chatbot]
    )

    msg.submit(
        respond,
        inputs=[msg, chatbot, system_prompt, use_rag, top_k, temperature],
        outputs=[msg, chatbot]
    )

    clear_btn.click(
        lambda: (None, []),
        outputs=[msg, chatbot]
    )