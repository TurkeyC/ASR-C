from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class BaseModel(ABC):
    """AI模型基类，所有具体模型实现需继承此类"""
    
    def __init__(self, model_name: str, temperature: float = 0.7):
        self.model_name = model_name
        self.temperature = temperature
        
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
    def get_available_models(self) -> List[str]:
        """获取可用模型列表"""
        pass