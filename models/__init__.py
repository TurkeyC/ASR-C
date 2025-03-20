from .base import BaseModel

def create_model(provider, model_name, api_key, api_base, temperature):
    """创建模型实例"""
    print(f"创建 {provider} 模型，基础URL: {api_base}，模型名称: {model_name}")

    if provider == "openai":
        from .openai_model import OpenAIModel
        return OpenAIModel(model_name, api_key, api_base, temperature)
    elif provider == "ollama":
        from .ollama_model import OllamaModel
        return OllamaModel(model_name, api_key, api_base, temperature)
    elif provider == "lmstudio":
        from .lmstudio_model import LMStudioModel
        return LMStudioModel(model_name, api_key, api_base, temperature)
    elif provider == "moonshot":
        from .moonshot_model import MoonshotModel
        return MoonshotModel(model_name, api_key, api_base, temperature)
    elif provider == "deepseek":
        from .deepseek_model import DeepseekModel
        return DeepseekModel(model_name, api_key, api_base, temperature)
    else:
        raise ValueError(f"不支持的模型提供商: {provider}")