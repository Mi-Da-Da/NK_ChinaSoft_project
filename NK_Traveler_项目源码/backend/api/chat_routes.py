from backend.services.search_service import SearchService
from backend.services.chat_service import ChatService
from backend.utils.helpers import load_history, save_message
from flask import Blueprint, request, jsonify, render_template

chat_bp = Blueprint('chat', __name__)
search_service = SearchService()
chat_service = ChatService(search_service)

@chat_bp.route('/')
def chat():
    """聊天页面"""
    history = load_history()
    return render_template('chat.html', history=history)

@chat_bp.route('/send', methods=['POST'])
def send():
    """发送消息"""
    user_msg = request.json.get('message', '')
    session_id = request.json.get('session_id', 1)
    search = request.json.get('search', False)
    rag = request.json.get('rag', False)
    
    bot_response = chat_service.process_message(user_msg, search=search, rag=rag)
    
    save_message('user', user_msg, session_id)
    save_message('bot', bot_response, session_id)
    
    return jsonify({"response": bot_response})

@chat_bp.route('/toggle_search', methods=['POST'])
def toggle_search():
    """切换实时搜索开关"""
    enabled = request.json.get('enabled', True)
    chat_service.search_service.set_search_enabled(enabled)
    return jsonify({
        "success": True, 
        "enabled": enabled,
        "message": f"实时搜索功能已{'启用' if enabled else '禁用'}"
    })

@chat_bp.route('/search_status', methods=['GET'])
def search_status():
    """获取实时搜索状态"""
    enabled = chat_service.search_service.is_search_enabled()
    return jsonify({
        "enabled": enabled,
        "available": chat_service.search_service.search_available
    })