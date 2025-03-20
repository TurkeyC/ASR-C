from typing import List, Dict, Any, Optional
import requests
import json
from .base import BaseModel

class DeepseekModel(BaseModel):
    """Deepseek API模型连接器"""

    def __init__(self, model_name: str, api_key: str, api_base: str = "https://api.deepseek.com/v1", temperature: float = 0.7):
        super().__init__(model_name, temperature)
        self.api_base = api_base
        self.api_key = api_key
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

    def chat(self,
             messages: List[Dict[str, str]],
             system_prompt: Optional[str] = None,
             temperature: Optional[float] = None) -> str:
        """使用Deepseek API进行聊天"""

        # 处理系统提示
        processed_messages = []
        if system_prompt:
            processed_messages.append({"role": "system", "content": system_prompt})

        # 添加消息历史
        processed_messages.extend(messages)

        # 准备API请求
        payload = {
            "model": self.model_name,
            "messages": processed_messages,
            "temperature": temperature if temperature is not None else self.temperature,
        }

        # 调用API
        response = requests.post(f"{self.api_base}/chat/completions",
                                headers=self.headers,
                                json=payload)

        if response.status_code != 200:
            raise Exception(f"API请求失败: {response.status_code} {response.text}")

        return response.json()["choices"][0]["message"]["content"]

    def get_available_models(self) -> List[str]:
        """获取可用的Deepseek模型列表"""
        try:
            response = requests.get(f"{self.api_base}/models", headers=self.headers)
            if response.status_code != 200:
                return ["deepseek-chat", "deepseek-coder"]

            models = response.json().get("data", [])
            return [model["id"] for model in models]
        except Exception as e:
            print(f"获取模型列表失败: {e}")
            return ["deepseek-chat", "deepseek-coder"]