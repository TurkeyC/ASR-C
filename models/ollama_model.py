from typing import List, Dict, Any, Optional
import requests
import json
from .base import BaseModel

class OllamaModel(BaseModel):
    """Ollama API模型连接器"""

    def __init__(self, model_name: str, api_key: str = None, api_base: str = "http://localhost:11434", temperature: float = 0.7):
        super().__init__(model_name, temperature)
        self.api_base = api_base

    def chat(self,
             messages: List[Dict[str, str]],
             system_prompt: Optional[str] = None,
             temperature: Optional[float] = None) -> str:
        """使用Ollama API进行聊天"""

        # 准备API请求
        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature if temperature is not None else self.temperature,
        }

        # 添加系统提示
        if system_prompt:
            payload["system"] = system_prompt

        # 调用API
        response = requests.post(f"{self.api_base}/api/chat",
                                json=payload)

        if response.status_code != 200:
            raise Exception(f"API请求失败: {response.status_code} {response.text}")

        return response.json()["message"]["content"]

    def get_available_models(self) -> List[str]:
        """获取可用的Ollama模型列表"""
        try:
            response = requests.get(f"{self.api_base}/api/tags")
            if response.status_code != 200:
                return ["llama2", "mistral", "llava"]

            models = response.json().get("models", [])
            return [model["name"] for model in models]
        except Exception as e:
            print(f"获取模型列表失败: {e}")
            return ["llama2", "mistral", "llava"]