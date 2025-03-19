import openai
from typing import List, Dict, Any, Optional
from .base import BaseModel

class OpenAIModel(BaseModel):
    """OpenAI API模型连接器"""
    
    def __init__(self, model_name: str, api_key: str, api_base: Optional[str] = None, temperature: float = 0.7):
        super().__init__(model_name, temperature)
        openai.api_key = api_key
        if api_base:
            openai.api_base = api_base
    
    def chat(self, 
             messages: List[Dict[str, str]], 
             system_prompt: Optional[str] = None,
             temperature: Optional[float] = None) -> str:
        """使用OpenAI API进行聊天"""
        
        # 处理系统提示
        processed_messages = []
        if system_prompt:
            processed_messages.append({"role": "system", "content": system_prompt})
        
        # 添加消息历史
        processed_messages.extend(messages)
        
        # 调用API
        response = openai.ChatCompletion.create(
            model=self.model_name,
            messages=processed_messages,
            temperature=temperature if temperature is not None else self.temperature
        )
        
        return response.choices[0].message.content
    
    def get_available_models(self) -> List[str]:
        """获取可用的OpenAI模型列表"""
        try:
            models = openai.Model.list()
            return [model.id for model in models.data if "gpt" in model.id]
        except Exception as e:
            print(f"获取模型列表失败: {e}")
            return ["gpt-3.5-turbo", "gpt-4"]