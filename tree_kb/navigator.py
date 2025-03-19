import os
import networkx as nx
from typing import Dict, List, Any, Optional, Tuple

class KnowledgeNavigator:
    """知识树导航器，用于在树状知识库中导航"""
    
    def __init__(self, tree_builder):
        self.tree_builder = tree_builder
        self.tree = tree_builder.get_tree()
    
    def refresh(self):
        """刷新知识树"""
        self.tree = self.tree_builder.get_tree()
    
    def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        """获取节点信息
        
        Args:
            node_id: 节点ID
            
        Returns:
            节点信息字典
        """
        if not self.tree.has_node(node_id):
            return None
        
        node_data = self.tree.nodes[node_id].copy()
        node_data["id"] = node_id
        return node_data
    
    def get_children(self, node_id: str) -> List[Dict[str, Any]]:
        """获取节点的子节点
        
        Args:
            node_id: 节点ID
            
        Returns:
            子节点列表
        """
        if not self.tree.has_node(node_id):
            return []
        
        children = []
        for child_id in self.tree.successors(node_id):
            node_data = self.tree.nodes[child_id].copy()
            node_data["id"] = child_id
            children.append(node_data)
        
        # 按类型和名称排序
        def sort_key(node):
            # 顺序: 目录 > 文件 > 标题
            type_order = {"directory": 0, "file": 1, "header": 2}
            return (type_order.get(node.get("type"), 99), node.get("name", ""))
            
        return sorted(children, key=sort_key)
    
    def get_path_to_node(self, node_id: str) -> List[Dict[str, Any]]:
        """获取从根节点到指定节点的路径
        
        Args:
            node_id: 目标节点ID
            
        Returns:
            路径上的节点列表
        """
        if not self.tree.has_node(node_id):
            return []
        
        path = []
        current = node_id
        
        # 逆向遍历到根节点
        while current != "root":
            # 获取当前节点的所有前驱节点
            predecessors = list(self.tree.predecessors(current))
            if not predecessors:
                break
                
            # 取第一个前驱（我们的树每个节点只有一个父节点）
            parent = predecessors[0]
            
            # 将当前节点添加到路径
            node_data = self.tree.nodes[current].copy()
            node_data["id"] = current
            path.append(node_data)
            
            # 移动到父节点
            current = parent
        
        # 添加根节点
        if current == "root":
            node_data = self.tree.nodes[current].copy()
            node_data["id"] = current
            path.append(node_data)
        
        # 反转路径，使其从根到目标
        return list(reversed(path))
    
    def search(self, query: str, max_results: int = 20) -> List[Dict[str, Any]]:
        """搜索知识树
        
        Args:
            query: 搜索查询
            max_results: 最大结果数
            
        Returns:
            匹配的节点列表
        """
        if not query:
            return []
            
        query = query.lower()
        results = []
        
        for node_id, node_data in self.tree.nodes(data=True):
            name = node_data.get("name", "")
            content = node_data.get("content", "")
            
            # 搜索名称和内容
            if query in name.lower() or query in content.lower():
                result = node_data.copy()
                result["id"] = node_id
                result["match_type"] = "name" if query in name.lower() else "content"
                results.append(result)
                
                if len(results) >= max_results:
                    break
        
        # 按匹配类型和名称排序
        def sort_key(node):
            match_type_order = {"name": 0, "content": 1}
            return (match_type_order.get(node.get("match_type"), 99), node.get("name", ""))
            
        return sorted(results, key=sort_key)
    
    def get_node_content(self, node_id: str) -> Optional[str]:
        """获取节点内容
        
        Args:
            node_id: 节点ID
            
        Returns:
            节点内容
        """
        node = self.get_node(node_id)
        if not node:
            return None
        
        node_type = node.get("type")
        
        if node_type == "header":
            # 对于标题节点，直接返回其内容
            return node.get("content", "")
        elif node_type == "file":
            # 对于文件节点，尝试读取文件内容
            path = node.get("path")
            if path:
                try:
                    file_path = os.path.join(self.tree_builder.documents_dir, path)
                    with open(file_path, "r", encoding="utf-8") as f:
                        return f.read()
                except Exception as e:
                    return f"无法读取文件内容: {str(e)}"
            return "文件路径不可用"
        else:
            # 对于其他类型节点，返回有关子节点的信息
            children = self.get_children(node_id)
            if not children:
                return "此节点没有内容"
            
            content = f"## {node.get('name', '未命名节点')}\n\n"
            content += "### 子节点:\n\n"
            
            for child in children:
                child_name = child.get("name", "未命名")
                child_type = child.get("type", "未知")
                content += f"- {child_name} ({child_type})\n"
                
            return content