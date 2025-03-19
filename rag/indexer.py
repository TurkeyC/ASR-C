import os
import uuid
from typing import List, Dict, Any, Optional
import re
from .vectorstore import VectorStore
from .retriever import Retriever

class DocumentIndexer:
    """文档索引器，用于索引和管理知识库文档"""
    
    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store
        self.retriever = Retriever(vector_store)
        
    def _split_markdown(self, content: str, max_chunk_size: int = 1000) -> List[str]:
        """将Markdown文档分割成适当大小的块
        
        Args:
            content: Markdown文本内容
            max_chunk_size: 每个块的最大字符数
            
        Returns:
            分割后的文档块列表
        """
        # 按标题分割
        header_pattern = r'^(#{1,6})\s+(.*?)$'
        lines = content.split('\n')
        chunks = []
        current_chunk = []
        current_size = 0
        
        for line in lines:
            # 检查是否是标题行
            header_match = re.match(header_pattern, line, re.M)
            
            # 如果是新标题或当前块太大，创建新块
            if (header_match and header_match.group(1) in ['#', '##', '###']) or current_size >= max_chunk_size:
                if current_chunk:
                    chunks.append('\n'.join(current_chunk))
                    current_chunk = []
                    current_size = 0
            
            # 添加当前行
            current_chunk.append(line)
            current_size += len(line)
        
        # 添加最后一个块
        if current_chunk:
            chunks.append('\n'.join(current_chunk))
        
        return chunks
    
    def index_file(self, file_path: str) -> List[str]:
        """索引单个Markdown文件
        
        Args:
            file_path: Markdown文件路径
            
        Returns:
            添加的文档ID列表
        """
        try:
            # 检查文件是否为Markdown
            if not file_path.endswith('.md'):
                print(f"跳过非Markdown文件: {file_path}")
                return []
            
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 分割文档
            chunks = self._split_markdown(content)
            
            # 存储元数据
            file_name = os.path.basename(file_path)
            metadata = {
                "source": file_path,
                "title": file_name,
                "type": "markdown"
            }
            
            # 为每个块创建索引
            doc_ids = []
            for i, chunk in enumerate(chunks):
                doc_id = f"{file_path}_{i}"
                
                # 为块添加额外元数据
                chunk_metadata = metadata.copy()
                chunk_metadata["chunk_index"] = i
                chunk_metadata["total_chunks"] = len(chunks)
                
                # 将文档添加到向量存储
                self.vector_store.add_document(doc_id, chunk, chunk_metadata)
                doc_ids.append(doc_id)
            
            print(f"已索引文件 {file_path}，共 {len(chunks)} 个块")
            return doc_ids
        
        except Exception as e:
            print(f"索引文件 {file_path} 失败: {e}")
            return []
    
    def index_directory(self, directory_path: str) -> Dict[str, List[str]]:
        """递归索引目录中的所有Markdown文件
        
        Args:
            directory_path: 要索引的目录路径
            
        Returns:
            文件路径到文档ID列表的映射
        """
        indexed_files = {}
        
        # 遍历目录
        for root, _, files in os.walk(directory_path):
            for file in files:
                if file.endswith('.md'):
                    file_path = os.path.join(root, file)
                    doc_ids = self.index_file(file_path)
                    if doc_ids:
                        indexed_files[file_path] = doc_ids
        
        return indexed_files
    
    def remove_file_index(self, file_path: str) -> bool:
        """移除文件的索引
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否成功移除
        """
        # 查询所有与此文件相关的文档ID
        to_remove = []
        for doc_id, doc_data in self.vector_store.documents.items():
            if doc_data["metadata"].get("source") == file_path:
                to_remove.append(doc_id)
        
        # 移除文档
        success = True
        for doc_id in to_remove:
            if not self.vector_store.delete_document(doc_id):
                success = False
        
        return success and len(to_remove) > 0
    
    def reindex(self, directory_path: str) -> Dict[str, List[str]]:
        """重新索引目录
        
        Args:
            directory_path: 要重新索引的目录路径
            
        Returns:
            文件路径到文档ID列表的映射
        """
        # 清空现有索引
        self.vector_store.documents = {}
        self.vector_store.embeddings = {}
        self.vector_store._save_to_disk()
        
        # 重新索引
        return self.index_directory(directory_path)
    
    def get_document_count(self) -> int:
        """获取已索引的文档数量"""
        return len(self.vector_store.documents)