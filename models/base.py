from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class BaseModel(ABC):
    """AI模型基类，所有具体模型实现需继承此类"""
    
    def __init__(self, model_name: str, temperature: float = 0.7):
        self.model_name = model_name
        self.temperature = temperature
        # 添加API key属性，方便子类访问
        self.api_key = ""

    @abstractmethod
    def chat(self, 
             messages: List[Dict[str, str]], 
             system_prompt: Optional[str] = None,
             temperature: Optional[float] = None) -> str:
        """处理聊天请求
        
        Args:
            messages: 消息列表，每条消息格式为 {"role": "user|assistant", "content": "文本内容"}
            system_prompt: 系统提示词
            temperature: 温度参数，覆盖默认值
            
        Returns:
            模型的回复文本
        """
        pass
    
    @abstractmethod
    def get_available_models(provider, api_key, api_base):
        if not provider or provider == "请选择":
            return []

        try:
            from models import create_model

            # 创建临时模型实例
            temp_model = create_model(
                provider=provider,
                model_name="moonshot-v1-8k" if provider == "moonshot" else "",  # 提供一个默认值
                api_key=api_key,
                api_base=api_base,
                temperature=0.7
            )

            # 获取可用模型列表
            models = temp_model.get_available_models()
            # 确保结果是字符串列表
            if isinstance(models, list) and all(isinstance(m, str) for m in models):
                return models
            else:
                raise ValueError("获取到的模型列表格式不正确")
        except Exception as e:
            print(f"获取模型列表失败: {e}")

            # 返回默认值
            if provider == "moonshot":
                return ["moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k"]
            elif provider == "openai":
                return ["gpt-3.5-turbo", "gpt-4"]
            elif provider == "ollama":
                return ["llama2", "mistral", "llava"]
            elif provider == "lmstudio":
                return ["Local Model"]
            elif provider == "deepseek":
                return ["deepseek-chat", "deepseek-coder"]
            else:
                return []

    def test_connection(self) -> tuple[bool, str]:
        """测试API连接，子类可以覆盖此方法"""
        try:
            # 简单的测试，尝试进行一次对话
            response = self.chat(
                messages=[{"role": "user", "content": "请回复 连接成功 用来测试API连接"}],
                system_prompt="你是一个测试助手，请简短回复"
            )
            return True, f"模型回复: {response}"
        except Exception as e:
            return False, f"连接测试失败: {str(e)}"