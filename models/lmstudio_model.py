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
        try:
            # 调用LMStudio API获取模型列表
            response = requests.get(f"{self.api_base}/models", headers=self.headers)

            if response.status_code != 200:
                print(f"获取模型列表失败: {response.status_code} {response.text}")
                return ["Local Model"]  # 返回默认值

            # 解析响应并提取模型ID
            models_data = response.json().get("data", [])
            model_names = [model.get("id") for model in models_data if model.get("id")]

            # 如果没有找到模型，返回默认值
            if not model_names:
                return ["Local Model"]

            return model_names

        except Exception as e:
            print(f"获取LMStudio模型列表失败: {e}")
            return ["Local Model"]  # 出错时返回默认值