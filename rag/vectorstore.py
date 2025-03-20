import os
import json
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
import openai

class VectorStore:
    """向量数据库，用于存储和检索文档嵌入"""
    
    def __init__(self, embedding_model: str, vector_dir: str):
        self.embedding_model = embedding_model
        self.vector_dir = vector_dir
        self.documents = {}  # 文档内容
        self.embeddings = {}  # 文档嵌入
        
        # 确保向量目录存在
        os.makedirs(vector_dir, exist_ok=True)
        
        # 加载已有的向量和文档
        self._load_from_disk()
        
    def _load_from_disk(self):
        """从磁盘加载向量和文档"""
        # 加载文档内容
        docs_path = os.path.join(self.vector_dir, "documents.json")
        if os.path.exists(docs_path):
            with open(docs_path, 'r', encoding='utf-8') as f:
                self.documents = json.load(f)
        
        # 加载向量嵌入
        embeddings_path = os.path.join(self.vector_dir, "embeddings.json")
        if os.path.exists(embeddings_path):
            with open(embeddings_path, 'r', encoding='utf-8') as f:
                embeddings_dict = json.load(f)
                # 将字符串列表转换回数值数组
                for doc_id, embedding_list in embeddings_dict.items():
                    self.embeddings[doc_id] = np.array(embedding_list, dtype=np.float32)
    
    def _save_to_disk(self):
        """将向量和文档保存到磁盘"""
        # 保存文档内容
        docs_path = os.path.join(self.vector_dir, "documents.json")
        with open(docs_path, 'w', encoding='utf-8') as f:
            json.dump(self.documents, f, ensure_ascii=False, indent=2)
        
        # 保存向量嵌入（转换为普通列表以便JSON序列化）
        embeddings_dict = {doc_id: embedding.tolist() for doc_id, embedding in self.embeddings.items()}
        embeddings_path = os.path.join(self.vector_dir, "embeddings.json")
        with open(embeddings_path, 'w', encoding='utf-8') as f:
            json.dump(embeddings_dict, f)
    
    # def get_embedding(self, text: str) -> np.ndarray:
    #     """获取文本的嵌入向量"""
    #     response = openai.Embedding.create(
    #         model=self.embedding_model,
    #         input=text
    #     )
    #     return np.array(response['data'][0]['embedding'], dtype=np.float32)
    def get_embedding(self, text: str) -> np.ndarray:
        """获取文本的嵌入向量"""
        if self.embedding_model.startswith("sentence-transformers/"):
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer(self.embedding_model)
            embedding = model.encode(text)
            # 转换为numpy数组
            return np.array(embedding, dtype=np.float32)
        else:
            # 原有的OpenAI逻辑，但使用新版API
            import openai
            client = openai.OpenAI()
            embeddings = client.embeddings.create(input=[text], model=self.embedding_model)
            return np.array(embeddings.data[0].embedding, dtype=np.float32)

    def add_document(self, doc_id: str, content: str, metadata: Dict[str, Any]):
        """添加文档到向量数据库"""
        # 存储文档内容和元数据
        self.documents[doc_id] = {
            "content": content,
            "metadata": metadata
        }
        
        # 获取并存储文档的嵌入向量
        self.embeddings[doc_id] = self.get_embedding(content)
        
        # 保存到磁盘
        self._save_to_disk()
    
    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """获取文档内容"""
        return self.documents.get(doc_id)
    
    def delete_document(self, doc_id: str) -> bool:
        """删除文档"""
        if doc_id in self.documents:
            del self.documents[doc_id]
            del self.embeddings[doc_id]
            self._save_to_disk()
            return True
        return False
    
    def similarity_search(self, query_embedding: np.ndarray, top_k: int = 5) -> List[Tuple[str, float]]:
        """基于余弦相似度搜索最相似的文档"""
        results = []
        
        # 计算每个文档与查询的余弦相似度
        for doc_id, doc_embedding in self.embeddings.items():
            # 归一化向量
            query_norm = np.linalg.norm(query_embedding)
            doc_norm = np.linalg.norm(doc_embedding)
            
            # 计算余弦相似度
            if query_norm > 0 and doc_norm > 0:
                similarity = np.dot(query_embedding, doc_embedding) / (query_norm * doc_norm)
                results.append((doc_id, similarity))
        
        # 按相似度降序排序并返回top_k个结果
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]