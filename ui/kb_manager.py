import gradio as gr
import os
from typing import Dict, List, Any

def create_kb_manager_ui(kb: Dict[str, Any]):
    """创建知识库管理界面"""
    
    # 获取知识库组件
    vector_store = kb["vector_store"]
    indexer = kb["indexer"]
    tree_builder = kb["tree_builder"]
    
    # 创建导航器
    from tree_kb.navigator import KnowledgeNavigator
    navigator = KnowledgeNavigator(tree_builder)
    
    # 当前选择的节点ID
    selected_node_id = gr.State("root")
    
    # 更新文件树展示
    def update_tree_view(node_id="root"):
        if not node_id:
            node_id = "root"
            
        # 获取当前节点信息
        node = navigator.get_node(node_id)
        if not node:
            return "节点不存在", "", []
        
        # 获取路径
        path = navigator.get_path_to_node(node_id)
        path_str = " > ".join([p.get("name", "未命名") for p in path])
        
        # 获取节点内容
        content = navigator.get_node_content(node_id)
        
        # 获取子节点列表
        children = navigator.get_children(node_id)
        child_items = []
        
        for child in children:
            child_id = child.get("id", "")
            child_name = child.get("name", "未命名")
            child_type = child.get("type", "未知")
            
            # 为不同类型设置不同图标
            icon = "📁" if child_type == "directory" else "📄" if child_type == "file" else "🔖"
            child_items.append(f"{icon} {child_name}|{child_id}")
        
        return path_str, content or "无内容", child_items
    
    # 处理节点选择
    def select_node(evt: gr.SelectData, items):
        if not items or evt.index >= len(items):
            return "root"
        
        # 解析节点ID
        selected = items[evt.index]
        parts = selected.split("|")
        if len(parts) != 2:
            return "root"
            
        return parts[1]
    
    # 搜索知识库
    def search_kb(query):
        if not query:
            return []
            
        results = navigator.search(query)
        formatted_results = []
        
        for result in results:
            node_id = result.get("id", "")
            name = result.get("name", "未命名")
            node_type = result.get("type", "未知")
            match_type = result.get("match_type", "")
            
            # 为不同类型设置不同图标
            icon = "📁" if node_type == "directory" else "📄" if node_type == "file" else "🔖"
            formatted_results.append(f"{icon} {name} ({match_type})|{node_id}")
            
        return formatted_results
    
    # 重建索引
    def rebuild_index(documents_dir):
        try:
            # 验证目录是否存在
            if not os.path.exists(documents_dir):
                return f"目录不存在: {documents_dir}"
                
            # 重建向量索引
            indexed = indexer.reindex(documents_dir)
            
            # 重建树状结构
            tree_builder.documents_dir = documents_dir
            tree_builder.build_tree()
            
            # 刷新导航器
            navigator.refresh()
            
            return f"成功重建索引，共处理了 {len(indexed)} 个文件"
        except Exception as e:
            return f"重建索引失败: {str(e)}"
    
    # 上传文件
    def upload_file(files, kb_dir):
        if not files:
            return "未选择文件"
            
        try:
            # 确保目录存在
            os.makedirs(kb_dir, exist_ok=True)
            
            # 处理上传的文件
            results = []
            for file in files:
                # 获取文件名
                filename = os.path.basename(file.name)
                
                # 构建目标路径
                target_path = os.path.join(kb_dir, filename)
                
                # 复制文件
                with open(target_path, "wb") as f:
                    f.write(file.read())
                
                # 索引文件
                if filename.endswith(".md"):
                    doc_ids = indexer.index_file(target_path)
                    results.append(f"文件 {filename} 已上传并索引，包含 {len(doc_ids)} 个文档块")
                else:
                    results.append(f"文件 {filename} 已上传（非Markdown文件，未索引）")
            
            # 重建树状结构
            tree_builder.build_tree()
            navigator.refresh()
            
            return "\n".join(results)
        except Exception as e:
            return f"上传文件失败: {str(e)}"
    
    # 获取统计信息
    def get_stats():
        doc_count = indexer.get_document_count()
        node_count = len(tree_builder.tree.nodes)
        return f"已索引 {doc_count} 个文档块, 知识树包含 {node_count} 个节点"
    
    # 创建UI
    with gr.Row():
        with gr.Column(scale=1):
            # 左侧：树形导航和搜索
            with gr.Accordion("知识库统计", open=True):
                stats_text = gr.Markdown(get_stats)
                refresh_stats = gr.Button("刷新统计")
            
            with gr.Accordion("搜索", open=True):
                search_input = gr.Textbox(placeholder="搜索知识库...", label="搜索查询")
                search_btn = gr.Button("搜索")
                search_results = gr.Radio([], label="搜索结果")
            
            with gr.Accordion("目录浏览", open=True):
                path_display = gr.Markdown("根目录")
                tree_items = gr.Radio([], label="子节点")
                back_btn = gr.Button("返回上级")
        
        with gr.Column(scale=2):
            # 右侧：内容展示和文件管理
            with gr.Accordion("节点内容", open=True):
                content_display = gr.Markdown("")
            
            with gr.Accordion("知识库管理", open=True):
                documents_dir = gr.Textbox(label="文档目录", 
                                          value="./knowledge/documents", 
                                          placeholder="输入文档目录路径...")
                rebuild_btn = gr.Button("重建索引")
                rebuild_status = gr.Markdown("")
                
                with gr.Row():
                    upload_files = gr.File(label="上传文件", file_count="multiple")
                    upload_btn = gr.Button("上传到知识库")
                upload_status = gr.Markdown("")
    
    # 设置事件处理
    refresh_stats.click(get_stats, outputs=stats_text)
    
    search_btn.click(
        search_kb,
        inputs=[search_input],
        outputs=[search_results]
    )
    
    search_results.select(
        lambda evt, items: items[evt.index].split("|")[1] if items and evt.index < len(items) else "root",
        inputs=[search_results],
        outputs=[selected_node_id]
    ).then(
        update_tree_view,
        inputs=[selected_node_id],
        outputs=[path_display, content_display, tree_items]
    )
    
    tree_items.select(
        select_node,
        inputs=[tree_items],
        outputs=[selected_node_id]
    ).then(
        update_tree_view,
        inputs=[selected_node_id],
        outputs=[path_display, content_display, tree_items]
    )
    
    back_btn.click(
        lambda path_str: "root" if path_str == "根目录" else navigator.get_path_to_node(selected_node_id.value)[
            -2]["id"] if len(navigator.get_path_to_node(selected_node_id.value)) > 1 else "root",
        inputs=[path_display],
        outputs=[selected_node_id]
    ).then(
        update_tree_view,
        inputs=[selected_node_id],
        outputs=[path_display, content_display, tree_items]
    )
    
    rebuild_btn.click(
        rebuild_index,
        inputs=[documents_dir],
        outputs=[rebuild_status]
    ).then(
        get_stats,
        outputs=[stats_text]
    ).then(
        lambda *args: "root",  # 修改为接收任意数量的参数
        outputs=[selected_node_id]
    ).then(
        update_tree_view,
        inputs=[selected_node_id],
        outputs=[path_display, content_display, tree_items]
    )
    
    upload_btn.click(
        upload_file,
        inputs=[upload_files, documents_dir],
        outputs=[upload_status]
    ).then(
        get_stats,
        outputs=[stats_text]
    )
    
    # 初始显示根节点
    selected_node_id.value = "root"
    path_str, content, items = update_tree_view("root")
    path_display.value = path_str
    content_display.value = content
    tree_items.choices = items