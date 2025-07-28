from flask import Blueprint, request, jsonify
from backend.services.weather_service import WeatherService
from backend.services.map_service import MapService
from backend.services.ai_service import AIService

weather_bp = Blueprint('weather', __name__)
weather_service = WeatherService()

map_service = MapService()
ai_service = AIService()

@weather_bp.route('/api/weather', methods=['GET'])
def get_weather():
    city = request.args.get('city', '').strip()
    days = int(request.args.get('days', 3))
    if not city:
        return jsonify({'success': False, 'message': '请提供城市名'}), 400
    current = weather_service.get_weather(city)
    forecast = weather_service.get_weather_forecast(city)
    days_data = []
    if isinstance(forecast, dict) and 'forecasts' in forecast and forecast['forecasts']:
        days_data = forecast['forecasts'][0].get('casts', [])[:days]
    return jsonify({'success': True, 'current': current, 'forecast': days_data})

@weather_bp.route('/api/route', methods=['GET'])
def get_route():
    origin = request.args.get('origin', '').strip()
    dest = request.args.get('dest', '').strip()
    mode = request.args.get('mode', 'driving').strip()
    if not origin or not dest:
        return jsonify({'success': False, 'message': '请提供起点和终点'}), 400
    route_info = map_service.get_route(origin, dest, mode)
    # 用大模型生成友好回答
    mode_map = {'driving': '驾车', 'transit': '公交', 'walking': '步行', 'riding': '骑行'}
    mode_cn = mode_map.get(mode, mode)
    prompt = f"请根据以下路线信息，帮我用简洁友好的语气推荐最优出行方式并说明理由：\n起点：{origin}\n终点：{dest}\n出行方式：{mode_cn}\n路线信息：{route_info}"
    try:
        answer = ai_service.invoke_ai(prompt)
    except Exception as e:
        answer = f"路线规划成功，但AI生成说明失败：{e}"
    return jsonify({'success': True, 'answer': answer}) 