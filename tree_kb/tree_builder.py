import os
import json
import re
from typing import Dict, List, Any, Optional
import networkx as nx

class KnowledgeTreeBuilder:
    """树状知识库构建器，用于构建文档的树状结构"""
    
    def __init__(self, documents_dir: str, tree_index_path: str):
        self.documents_dir = documents_dir
        self.tree_index_path = tree_index_path
        self.tree = nx.DiGraph()
        
        # 如果索引文件存在，加载现有树
        if os.path.exists(tree_index_path):
            self._load_tree()
    
    def _load_tree(self):
        """从文件加载树状结构"""
        try:
            with open(self.tree_index_path, 'r', encoding='utf-8') as f:
                tree_data = json.load(f)
            
            # 重建图
            self.tree = nx.node_link_graph(tree_data)
        except Exception as e:
            print(f"加载树状索引失败: {e}")
            self.tree = nx.DiGraph()
    
    def _save_tree(self):
        """保存树状结构到文件"""
        # 确保目录存在
        os.makedirs(os.path.dirname(self.tree_index_path), exist_ok=True)
        
        # 将图转换为可序列化格式并保存
        tree_data = nx.node_link_data(self.tree)
        with open(self.tree_index_path, 'w', encoding='utf-8') as f:
            json.dump(tree_data, f, ensure_ascii=False, indent=2)
    
    def _extract_headers(self, content: str) -> List[Dict[str, Any]]:
        """从Markdown内容中提取标题结构"""
        headers = []
        lines = content.split('\n')
        
        for line in lines:
            # 匹配Markdown标题
            match = re.match(r'^(#{1,6})\s+(.*?)(?:\s+\{#(.*?)\})?\s*$', line)
            if match:
                level = len(match.group(1))  # #的数量表示层级
                title = match.group(2).strip()
                anchor = match.group(3) if match.group(3) else None
                
                headers.append({
                    "level": level,
                    "title": title,
                    "anchor": anchor,
                    "line": line
                })
                
        return headers
    
    def build_tree(self):
        """构建知识库的树状结构"""
        # 重置树
        self.tree = nx.DiGraph()
        
        # 添加根节点
        root_id = "root"
        self.tree.add_node(root_id, name="知识库根目录", type="root")
        
        # 遍历文档目录
        for root, dirs, files in os.walk(self.documents_dir):
            # 创建目录节点
            rel_path = os.path.relpath(root, self.documents_dir)
            if rel_path == ".":
                parent_id = root_id
            else:
                dir_id = f"dir:{rel_path}"
                dir_name = os.path.basename(root)
                parent_dir = os.path.dirname(rel_path)
                parent_id = f"dir:{parent_dir}" if parent_dir != "." else root_id
                
                # 添加目录节点和边
                if not self.tree.has_node(dir_id):
                    self.tree.add_node(dir_id, name=dir_name, type="directory", path=rel_path)
                    self.tree.add_edge(parent_id, dir_id)
            
            # 处理文件
            for file in files:
                if file.endswith('.md'):
                    file_path = os.path.join(root, file)
                    rel_file_path = os.path.relpath(file_path, self.documents_dir)
                    file_id = f"file:{rel_file_path}"
                    
                    # 添加文件节点
                    self.tree.add_node(file_id, name=file, type="file", path=rel_file_path)
                    self.tree.add_edge(parent_id, file_id)
                    
                    # 读取文件内容
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # 提取标题结构
                        headers = self._extract_headers(content)
                        
                        # 构建文件内部的标题树
                        if headers:
                            header_stack = [(0, file_id)]  # (level, node_id)
                            
                            for i, header in enumerate(headers):
                                header_id = f"{file_id}#h{i}"
                                level = header["level"]
                                
                                # 找到当前标题的父节点
                                while header_stack and header_stack[-1][0] >= level:
                                    header_stack.pop()
                                
                                parent_id = header_stack[-1][1] if header_stack else file_id
                                
                                # 添加标题节点
                                self.tree.add_node(
                                    header_id, 
                                    name=header["title"], 
                                    type="header", 
                                    level=level,
                                    path=f"{rel_file_path}#{header['anchor'] if header['anchor'] else ''}",
                                    content=header["line"]
                                )
                                self.tree.add_edge(parent_id, header_id)
                                
                                # 将当前标题加入堆栈
                                header_stack.append((level, header_id))
                    except Exception as e:
                        print(f"处理文件 {file_path} 失败: {e}")
        
        # 保存树状结构
        self._save_tree()
    
    def get_tree(self):
        """获取构建的知识树"""
        return self.tree
    
    def get_node_children(self, node_id: str) -> List[Dict[str, Any]]:
        """获取节点的所有子节点"""
        if not self.tree.has_node(node_id):
            return []
        
        children = []
        for child_id in self.tree.successors(node_id):
            node_data = self.tree.nodes[child_id]
            children.append({
                "id": child_id,
                "name": node_data.get("name", ""),
                "type": node_data.get("type", ""),
                "path": node_data.get("path", "")
            })
        
        return children
    
    def search_nodes(self, query: str) -> List[Dict[str, Any]]:
        """搜索树中的节点"""
        results = []
        
        for node_id in self.tree.nodes:
            node_data = self.tree.nodes[node_id]
            name = node_data.get("name", "")
            
            if query.lower() in name.lower():
                results.append({
                    "id": node_id,
                    "name": name,
                    "type": node_data.get("type", ""),
                    "path": node_data.get("path", "")
                })
        
        return results