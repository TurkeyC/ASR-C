from typing import List, Dict, Any, Optional
import os
import json
from .vectorstore import VectorStore

class Retriever:
    """文档检索器，用于从向量数据库中检索相关文档"""
    
    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store
        
    def retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """检索与查询最相关的文档
        
        Args:
            query: 用户查询
            top_k: 返回的最大文档数量
            
        Returns:
            相关文档列表，每个文档包含内容、路径、相关度分数等
        """
        # 获取查询的向量表示
        query_embedding = self.vector_store.get_embedding(query)
        
        # 从向量数据库检索相似文档
        results = self.vector_store.similarity_search(query_embedding, top_k)
        
        # 格式化返回结果
        formatted_results = []
        for doc_id, score in results:
            doc_data = self.vector_store.get_document(doc_id)
            if doc_data:
                formatted_results.append({
                    "content": doc_data["content"],
                    "metadata": doc_data["metadata"],
                    "score": float(score)
                })
                
        return formatted_results
    
    def get_retrieval_context(self, query: str, top_k: int = 5) -> str:
        """获取检索上下文作为字符串
        
        Args:
            query: 用户查询
            top_k: 返回的最大文档数量
            
        Returns:
            合并后的上下文字符串
        """
        results = self.retrieve(query, top_k)
        
        # 构建上下文
        context_parts = []
        for i, result in enumerate(results, 1):
            source = result["metadata"].get("source", "未知来源")
            context_parts.append(f"[文档 {i} (来源: {source})]\n{result['content']}\n")
        
        return "\n".join(context_parts)