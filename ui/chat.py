import gradio as gr
import time
from typing import Dict, List, Any
from models.base import BaseModel
import re

def create_chat_ui(model: BaseModel, kb: Dict[str, Any]):
    """创建聊天界面"""

    custom_css = """
    <style>
    .chat-display .message-wrap {
        overflow-x: auto !important;
    }
    .chat-display .message-wrap .message {
        max-width: 100% !important;
        overflow-x: auto !important;
    }
    .chat-display .message-wrap .message p {
        white-space: pre-wrap !important;
    }
    .chat-display .message .math-block {
        overflow-x: auto !important;
        padding: 8px 0 !important;
        margin: 8px 0 !important;
    }
    </style>
    """
    gr.HTML(custom_css)

    # 获取知识库组件
    vector_store = kb["vector_store"]
    retriever = kb["indexer"].retriever
    tree_builder = kb["tree_builder"]

    # 全局聊天历史记录
    chat_history = []

    # 处理LaTeX公式的函数，确保行间公式能正确显示
    def process_latex_formulas(text):
        """处理文本中的LaTeX公式，确保正确渲染"""
        if not text:
            return text

        # 更精确的正则表达式，使用非贪婪匹配并考虑嵌套和转义
        result = ""
        last_end = 0

        # 使用更可靠的正则表达式找出所有行间公式
        for match in re.finditer(r'(^|\n)[ \t]*(\$\$)(.+?)(\$\$)[ \t]*($|\n)', text, re.DOTALL | re.MULTILINE):
            start, end = match.span()
            formula_content = match.group(3).strip()

            # 添加匹配前的文本
            result += text[last_end:start]

            # 添加格式化的公式，确保前后有两个空行
            result += f"\n\n$$\n{formula_content}\n$$\n\n"

            last_end = end

        # 添加最后一段文本
        if last_end < len(text):
            result += text[last_end:]

        # 如果没有匹配项，返回原始文本
        if result == "":
            # 第二种尝试：处理不符合上面格式的公式
            pattern = r'(\$\$)(.*?)(\$\$)'

            def replace_formula(match):
                formula = match.group(2).strip()
                return f"\n\n$$\n{formula}\n$$\n\n"

            result = re.sub(pattern, replace_formula, text, flags=re.DOTALL)

        return result

    # 处理用户消息
    def respond(message, history, system_prompt, use_rag, top_k, temperature):
        try:
            # 打印当前模型配置进行调试
            print(f"使用模型: {model.model_name}")
            print(f"API基础URL: {getattr(model, 'api_base', 'N/A')}")

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
            latex_prompt = """
            在回答涉及数学公式时，请使用LaTeX语法，请确保只使用行内公式，不应该使用行间公式，这对于正确渲染非常重要。
            """
            if system_prompt:
                system_prompt += "\n\n" + latex_prompt
            else:
                system_prompt = latex_prompt

            # 获取模型回复
            reply = model.chat(
                messages=current_chat_history,
                system_prompt=system_prompt,
                temperature=float(temperature)
            )

            # 确保reply是字符串
            if not isinstance(reply, str):
                reply = str(reply)

            # 处理回复中的LaTeX公式，确保正确渲染
            reply = process_latex_formulas(reply)

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
            # 主聊天区域 - 启用Markdown和LaTeX渲染
            chatbot = gr.Chatbot(
                height=600,
                render_markdown=True,
                latex_delimiters=[
                    {"left": "$$", "right": "$$", "display": True},
                    {"left": "$", "right": "$", "display": False}
                ],
                bubble_full_width=False,  # 确保气泡不会占满宽度，有助于公式渲染
                elem_classes="chat-display"  # 添加自定义类以便于样式定制
            )

            # 提示用户可以使用LaTeX
            msg = gr.Textbox(
                placeholder="在此输入您的问题...（支持LaTeX公式）",
                lines=3
            )

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