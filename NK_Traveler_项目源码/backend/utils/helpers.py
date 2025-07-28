import json
import os
from backend.config.settings import Config

def load_history():
    """加载聊天历史"""
    if os.path.exists(Config.HISTORY_FILE):
        with open(Config.HISTORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_message(role, message, session_id=1):
    """保存消息到历史记录"""
    sessions = load_history()
    
    for s in sessions:
        if s["id"] == session_id:
            s["history"].append({"role": role, "message": message})
            break
    else:
        sessions.append({
            "id": session_id,
            "title": f"会话{session_id}",
            "history": [{"role": role, "message": message}]
        })
    
    # 确保目录存在
    os.makedirs(os.path.dirname(Config.HISTORY_FILE), exist_ok=True)
    
    with open(Config.HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(sessions, f, ensure_ascii=False, indent=2)

def delete_session_by_id(session_id):
    """根据 session_id 删除会话"""
    sessions = load_history()
    sessions = [s for s in sessions if s["id"] != session_id]
    # 确保目录存在
    os.makedirs(os.path.dirname(Config.HISTORY_FILE), exist_ok=True)
    with open(Config.HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(sessions, f, ensure_ascii=False, indent=2)

def clear_all_sessions():
    """清空所有聊天记录（会话）"""
    from backend.config.settings import Config
    import os, json
    # 确保目录存在
    os.makedirs(os.path.dirname(Config.HISTORY_FILE), exist_ok=True)
    with open(Config.HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump([], f, ensure_ascii=False, indent=2)