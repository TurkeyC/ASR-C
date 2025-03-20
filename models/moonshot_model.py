from typing import List, Dict, Any, Optional
import requests
import json
from .base import BaseModel

def __init__(self, model_name: str, api_key: str, api_base: str = "https://api.moonshot.cn/v1", temperature: float = 0.7):
    # 处理model_name可能是列表的情况
    if isinstance(model_name, list) and len(model_name) > 0:
        model_name = model_name[0]

    super().__init__(model_name, temperature)
    # 使用传入的api_base而非硬编码值
    self.api_base = api_base if api_base else "https://api.moonshot.cn/v1"
    self.api_key = api_key
    self.headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

class MoonshotModel(BaseModel):
    """Moonshot API模型连接器"""

    def __init__(self, model_name: str, api_key: str, api_base: str = "https://api.moonshot.cn/v1", temperature: float = 0.7):
        super().__init__(model_name, temperature)
        self.api_base = "https://api.moonshot.cn/v1"
        self.api_key = api_key
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

    def chat(self,
             messages: List[Dict[str, str]],
             system_prompt: Optional[str] = None,
             temperature: Optional[float] = None) -> str:
        """使用Moonshot API进行聊天"""

        # 处理系统提示
        processed_messages = []
        if system_prompt:
            processed_messages.append({"role": "system", "content": system_prompt})

        # 添加消息历史（确保格式正确）
        for msg in messages:
            if isinstance(msg, dict) and "role" in msg and "content" in msg:
                processed_messages.append(msg)

        # 打印请求信息以便调试
        print(f"发送请求到Moonshot API: {processed_messages}")
        print(f"API基础URL: {self.api_base}")
        print(f"认证头部: Authorization: Bearer {self.api_key[:4]}...{self.api_key[-4:] if len(self.api_key) > 8 else ''}")
        print(f"模型名称: {self.model_name}")

        # 准备API请求
        payload = {
            "model": self.model_name,
            "messages": processed_messages,
            "temperature": temperature if temperature is not None else self.temperature,
        }

        try:
            # 调用API
            response = requests.post(
                f"{self.api_base}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=30  # 设置超时
            )

            # 检查响应状态
            if response.status_code != 200:
                print(f"API响应错误，状态码: {response.status_code}")
                print(f"响应内容: {response.text}")
                raise Exception(f"API请求失败: {response.status_code} {response.text}")

            # 获取并验证响应内容
            response_json = response.json()
            print(f"API响应: {response_json}")

            if "choices" not in response_json or not response_json["choices"]:
                raise Exception(f"API响应格式错误: {response_json}")

            content = response_json["choices"][0]["message"]["content"]
            return content

        except Exception as e:
            print(f"Moonshot API错误: {str(e)}")
            raise e

    def get_available_models(self) -> List[str]:
        """获取可用的Moonshot模型列表"""
        try:
            response = requests.get(f"{self.api_base}/models", headers=self.headers)
            if response.status_code != 200:
                return ["moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k"]

            models = response.json().get("data", [])
            return [model["id"] for model in models]
        except Exception as e:
            print(f"获取模型列表失败: {e}")
            return ["moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k"]

    def test_connection(self) -> tuple[bool, str]:
        """测试API连接"""
        try:
            # 使用一个简单请求测试连接
            payload = {
                "model": self.model_name,  # 确保这是字符串
                "messages": [{"role": "user", "content": "Hello"}],
                "temperature": self.temperature
            }

            response = requests.post(
                f"{self.api_base}/chat/completions",
                headers=self.headers,
                json=payload
            )

            if response.status_code != 200:
                return False, f"API请求失败: {response.status_code} {response.text}"

            return True, "连接成功"
        except Exception as e:
            return False, f"连接测试失败: {str(e)}"