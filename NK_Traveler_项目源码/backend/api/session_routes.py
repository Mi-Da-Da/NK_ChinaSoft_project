from flask import Blueprint, request, jsonify
from backend.utils.helpers import load_history, save_message

session_bp = Blueprint('session', __name__)

@session_bp.route('/sessions', methods=['GET'])
def get_sessions():
    """获取所有会话列表"""
    sessions = load_history()
    session_list = [{"id": s["id"], "title": s["title"]} for s in sessions]
    return jsonify(session_list)

@session_bp.route('/session/<int:session_id>', methods=['GET'])
def get_session(session_id):
    """获取指定会话的历史记录"""
    sessions = load_history()
    for s in sessions:
        if s["id"] == session_id:
            return jsonify(s["history"])
    return jsonify([]), 404

@session_bp.route('/session/<int:session_id>', methods=['DELETE'])
def delete_session(session_id):
    """删除指定会话"""
    from backend.utils.helpers import delete_session_by_id
    delete_session_by_id(session_id)
    return jsonify({"success": True, "message": f"会话 {session_id} 已删除"})

@session_bp.route('/session/new', methods=['POST'])
def new_session():
    """创建新会话"""
    sessions = load_history()
    new_id = max(s["id"] for s in sessions) + 1 if sessions else 1
    title = request.json.get('title', f'会话{new_id}')
    
    sessions.append({"id": new_id, "title": title, "history": []})
    
    from backend.config.settings import Config
    import json
    import os
    
    # 确保目录存在
    os.makedirs(os.path.dirname(Config.HISTORY_FILE), exist_ok=True)
    
    with open(Config.HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(sessions, f, ensure_ascii=False, indent=2)
    
    return jsonify({"id": new_id, "title": title})

@session_bp.route('/session/<int:session_id>/rename', methods=['POST'])
def rename_session(session_id):
    new_title = request.json.get('title', '').strip()
    if not new_title:
        return jsonify({'success': False, 'message': '标题不能为空'}), 400
    sessions = load_history()
    for s in sessions:
        if s['id'] == session_id:
            s['title'] = new_title
            break
    else:
        return jsonify({'success': False, 'message': '会话不存在'}), 404
    from backend.config.settings import Config
    import json, os
    os.makedirs(os.path.dirname(Config.HISTORY_FILE), exist_ok=True)
    with open(Config.HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(sessions, f, ensure_ascii=False, indent=2)
    return jsonify({'success': True, 'title': new_title})

@session_bp.route('/sessions/clear', methods=['POST'])
def clear_sessions():
    """清空所有聊天记录（会话）"""
    from backend.utils.helpers import clear_all_sessions
    clear_all_sessions()
    return jsonify({"success": True, "message": "所有聊天记录已清空"})