import gradio as gr
import yaml
import os
from typing import Dict, Any
from models.base import BaseModel

def create_settings_ui(config: Dict[str, Any], model: BaseModel):
    """创建设置界面"""

    # 声明model为非本地变量，以便可以修改它
    global_model = model

    # 保存配置
    def save_config(provider, model_name, api_key, api_base, temperature,
                  embedding_model, documents_dir, vector_dir, tree_index_path,
                  auto_index, incremental_index, auto_build_tree):
        try:
            from models import create_model

            # 更新配置
            new_config = {
                "model": {
                    "provider": provider,
                    "name": model_name,
                    "api_key": api_key,
                    "api_base": api_base,
                    "temperature": float(temperature)
                },
                "knowledge_base": {
                    "embedding_model": embedding_model,
                    "documents_dir": documents_dir,
                    "vector_dir": vector_dir,
                    "tree_index_path": tree_index_path,
                    "auto_index": bool(auto_index),
                    "incremental_index": bool(incremental_index),
                    "auto_build_tree": bool(auto_build_tree)
                },
                "ui": config.get("ui", {"theme": "soft", "title": "AI助手", "max_history": 10})
            }

            # 写入配置文件
            with open("config.yaml", "w", encoding="utf-8") as f:
                yaml.dump(new_config, f, default_flow_style=False, allow_unicode=True)

            # 重要：重新创建模型实例
            try:
                nonlocal global_model
                # 创建新的模型实例
                new_model = create_model(
                    provider=provider,
                    model_name=model_name,
                    api_key=api_key,
                    api_base=api_base,
                    temperature=float(temperature)
                )

                # 替换全局模型实例的属性
                global_model.model_name = new_model.model_name
                global_model.temperature = new_model.temperature

                # 复制所有属性
                for attr_name in dir(new_model):
                    if not attr_name.startswith('__'):
                        try:
                            setattr(global_model, attr_name, getattr(new_model, attr_name))
                        except:
                            pass

                return "配置已保存并应用，模型已更新！您可以直接使用新模型。"
            except Exception as e:
                return f"配置已保存，但更新模型实例失败: {str(e)}。请重启应用以应用更改。"

        except Exception as e:
            return f"保存配置失败: {str(e)}"

    # 测试模型连接
    def test_model_connection(provider, model_name, api_key, api_base):
        from models import create_model

        try:
            # 确保model_name是字符串
            if isinstance(model_name, list) and len(model_name) > 0:
                model_name = model_name[0]

            # 创建模型实例
            test_model = create_model(
                provider=provider,
                model_name=model_name,
                api_key=api_key,
                api_base=api_base,
                temperature=0.7
            )

            # 如果模型有test_connection方法，则使用它
            if hasattr(test_model, 'test_connection'):
                success, message = test_model.test_connection()
                if success:
                    return "连接测试成功！" + message
                else:
                    return message

            # 否则使用chat方法测试连接
            response = test_model.chat(
                messages=[{"role": "user", "content": "请回复 连接成功 用来测试API连接"}],
                system_prompt="你是一个测试助手，请简短回复"
            )

            return f"连接测试成功！模型回复: {response}"
        except Exception as e:
            return f"连接测试失败: {str(e)}"

    # 获取可用模型
    def get_available_models(provider, api_key, api_base):
        if not provider or provider == "请选择":
            return gr.update(choices=[], value="")

        try:
            from models import create_model

            # 创建临时模型实例
            temp_model = create_model(
                provider=provider,
                model_name="Local Model" if provider == "lmstudio" else "",
                api_key=api_key,
                api_base=api_base,
                temperature=0.7
            )

            # 获取可用模型列表
            models = temp_model.get_available_models()
            print(f"从 {provider} 获取到的模型列表: {models}")  # 调试输出

            # 确保结果为非空列表
            if not models or not isinstance(models, list) or len(models) == 0:
                # 返回默认值
                if provider == "openai":
                    models = ["gpt-3.5-turbo", "gpt-4"]
                elif provider == "ollama":
                    models = ["llama2", "mistral", "llava"]
                elif provider == "lmstudio":
                    models = ["Local Model"]
                elif provider == "moonshot":
                    models = ["moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k"]
                elif provider == "deepseek":
                    models = ["deepseek-chat", "deepseek-coder"]
                else:
                    models = []

            # 返回一个gr.update对象，而不是直接返回列表
            return gr.update(choices=models, value=models[0] if models else "")

        except Exception as e:
            print(f"获取模型列表失败: {e}")
            import traceback
            traceback.print_exc()

            # 返回默认值
            default_models = {
                "openai": ["gpt-3.5-turbo", "gpt-4"],
                "ollama": ["llama2", "mistral", "llava"],
                "lmstudio": ["Local Model"],
                "moonshot": ["moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k"],
                "deepseek": ["deepseek-chat", "deepseek-coder"]
            }
            models = default_models.get(provider, [])
            return gr.update(choices=models, value=models[0] if models else "")

    # 创建UI
    with gr.Row():
        with gr.Column():
            # 模型设置
            with gr.Accordion("模型设置", open=True):
                provider = gr.Dropdown(
                    ["openai", "ollama", "lmstudio", "moonshot", "deepseek"],
                    label="模型提供商",
                    value=config["model"]["provider"]
                )
                api_key = gr.Textbox(
                    value=config["model"].get("api_key", ""),
                    label="API密钥",
                    type="password",
                    placeholder="输入API密钥（OpenAI需要）"
                )
                api_base = gr.Textbox(
                    value=config["model"].get("api_base", ""),
                    label="API基础URL",
                    placeholder="输入自定义API基础URL"
                )
                update_models_btn = gr.Button("获取可用模型列表")
                model_name = gr.Dropdown(
                    [],
                    label="模型名称",
                    value=config["model"]["name"],
                    allow_custom_value=True,
                    interactive=True  # 确保可交互
                )
                temperature = gr.Slider(
                    minimum=0,
                    maximum=1,
                    step=0.1,
                    value=config["model"].get("temperature", 0.7),
                    label="温度参数"
                )
                test_conn_btn = gr.Button("测试连接")
                test_result = gr.Markdown("")

            # 知识库设置
            with gr.Accordion("知识库设置", open=True):
                embedding_model = gr.Textbox(
                    value=config["knowledge_base"]["embedding_model"],
                    label="嵌入模型",
                    placeholder="输入嵌入模型名称"
                )
                documents_dir = gr.Textbox(
                    value=config["knowledge_base"]["documents_dir"],
                    label="文档目录",
                    placeholder="输入文档目录路径"
                )
                vector_dir = gr.Textbox(
                    value=config["knowledge_base"]["vector_dir"],
                    label="向量存储目录",
                    placeholder="输入向量存储目录路径"
                )
                tree_index_path = gr.Textbox(
                    value=config["knowledge_base"]["tree_index_path"],
                    label="树状索引路径",
                    placeholder="输入树状索引文件路径"
                )

                with gr.Row():
                    auto_index = gr.Checkbox(
                        value=config["knowledge_base"].get("auto_index", True),
                        label="自动索引文档"
                    )
                    incremental_index = gr.Checkbox(
                        value=config["knowledge_base"].get("incremental_index", True),
                        label="增量索引（仅处理修改过的文件）"
                    )
                    auto_build_tree = gr.Checkbox(
                        value=config["knowledge_base"].get("auto_build_tree", True),
                        label="自动构建树状结构"
                    )

            # 保存按钮
            save_btn = gr.Button("保存配置")
            save_result = gr.Markdown("")

    # 设置事件处理
    update_models_btn.click(
        get_available_models,
        inputs=[provider, api_key, api_base],
        outputs=[model_name]
    )

    test_conn_btn.click(
        test_model_connection,
        inputs=[provider, model_name, api_key, api_base],
        outputs=[test_result]
    )

    save_btn.click(
        save_config,
        inputs=[
            provider, model_name, api_key, api_base, temperature,
            embedding_model, documents_dir, vector_dir, tree_index_path,
            auto_index, incremental_index, auto_build_tree  # 添加incremental_index参数
        ],
        outputs=[save_result]
    )

    # 根据提供商动态显示/隐藏字段
    def update_api_visibility(provider):
        if provider == "openai" or provider == "moonshot" or provider == "deepseek":
            return gr.update(visible=True), gr.update(visible=True)
        elif provider == "lmstudio":
            return gr.update(visible=False), gr.update(visible=True)
        elif provider == "ollama":
            return gr.update(visible=False), gr.update(visible=True)
        else:
            return gr.update(visible=False), gr.update(visible=False)