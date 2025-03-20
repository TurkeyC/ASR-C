from typing import List, Dict, Any, Optional
import requests
import json
from .base import BaseModel

class LMStudioModel(BaseModel):
    """LMStudio API模型连接器"""

    def __init__(self, model_name: str = "Local Model", api_key: str = None, api_base: str = "http://localhost:1234/v1", temperature: float = 0.7):
        super().__init__(model_name, temperature)
        self.api_base = api_base
        self.headers = {"Content-Type": "application/json"}
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"

    def chat(self,
             messages: List[Dict[str, str]],
             system_prompt: Optional[str] = None,
             temperature: Optional[float] = None) -> str:
        """使用LMStudio API进行聊天"""

        # 处理系统提示
        processed_messages = []
        if system_prompt:
            processed_messages.append({"role": "system", "content": system_prompt})

        # 添加消息历史
        processed_messages.extend(messages)

        # 准备API请求
        payload = {
            "messages": processed_messages,
            "temperature": temperature if temperature is not None else self.temperature,
            "model": self.model_name
        }

        # 调用API
        response = requests.post(f"{self.api_base}/chat/completions",
                                headers=self.headers,
                                data=json.dumps(payload))

        if response.status_code != 200:
            raise Exception(f"API请求失败: {response.status_code} {response.text}")

        return response.json()["choices"][0]["message"]["content"]

    def get_available_models(self) -> List[str]:
        """获取可用的LMStudio模型列表"""
        # LMStudio通常只有一个本地模型
        return ["Local Model"]