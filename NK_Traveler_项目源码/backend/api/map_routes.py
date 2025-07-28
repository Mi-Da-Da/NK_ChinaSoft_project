from flask import Blueprint, request, jsonify
from backend.services.map_service import MapService

map_bp = Blueprint('map', __name__)
map_service = MapService()

@map_bp.route('/search', methods=['POST'])
def amap_search():
    """专门处理高德地图搜索请求"""
    data = request.json
    user_input = data.get('query', '')
    
    if not user_input:
        return jsonify({"error": "请提供搜索关键词"}), 400
    
    try:
        result = map_service.process_search_request(user_input)
        return jsonify({"result": result})
    except Exception as e:
        return jsonify({"error": f"搜索失败：{str(e)}"}), 500

@map_bp.route('/route', methods=['POST'])
def amap_route():
    """处理路线规划请求"""
    data = request.json
    origin = data.get('origin')
    destination = data.get('destination')
    strategy = data.get('strategy', 0)
    
    if not origin or not destination:
        return jsonify({"error": "请提供起点和终点"}), 400
    
    try:
        result = map_service.get_route(origin, destination, strategy)
        return jsonify({"result": result})
    except Exception as e:
        return jsonify({"error": f"路线规划失败：{str(e)}"}), 500