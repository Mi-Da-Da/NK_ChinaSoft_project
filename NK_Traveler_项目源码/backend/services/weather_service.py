import requests
import re
from langchain.schema import HumanMessage
from backend.services.ai_service import AIService
from backend.config.settings import Config

class WeatherService:
    """天气服务类"""
    
    def __init__(self):
        self.ai_service = AIService()
    
    def get_weather(self, city):
        """获取当前天气"""
        url = f"{Config.AMAP_BASE_URL}/weather/weatherInfo"
        params = {
            'key': Config.AMAP_API_KEY,
            'city': city,
            'extensions': 'base'
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            result = response.json()
            if result.get('status') == '1':
                weather_data = result.get('lives', [{}])[0]
                return f"{weather_data.get('city', '')}：{weather_data.get('weather', '')}，温度{weather_data.get('temperature', '')}℃，{weather_data.get('winddirection', '')}风{weather_data.get('windpower', '')}级，湿度{weather_data.get('humidity', '')}%"
            return f"获取{city}天气信息失败"
        except Exception as e:
            return f"获取{city}天气信息失败：{e}"
    
    def get_weather_forecast(self, city):
        """获取天气预报"""
        url = f"{Config.AMAP_BASE_URL}/weather/weatherInfo"
        params = {
            'key': Config.AMAP_API_KEY,
            'city': city,
            'extensions': 'all'
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return f"获取{city}天气预报失败：{e}"
    
    def process_weather_request(self, user_input):
        """处理天气相关请求 - 按照原来的完整逻辑"""
        from backend.services.keyword_service import extract_with_attractions
        
        # 提取城市信息
        travel_info = extract_with_attractions(user_input, self.ai_service.chatLLM)
        city = travel_info.get("destination")
        weather_city = city or "北京"
        
        weather = self.get_weather(weather_city)
        forecast = self.get_weather_forecast(weather_city)
        
        match = re.search(r"(?:近|未来)?(\d+)天", user_input)
        if match:
            n_days = int(match.group(1))
            if n_days > 4:
                n_days = 4
            if isinstance(forecast, dict) and "forecasts" in forecast and forecast["forecasts"]:
                days_data = forecast["forecasts"][0].get("casts", [])[:n_days]
            else:
                days_data = []
            print(f"days_data长度: {len(days_data)}，内容: {days_data}")
            days_text = ""
            for day in days_data:
                days_text += f"- {day['date']}：{day['dayweather']}，最高{day['daytemp']}℃，最低{day['nighttemp']}℃，{day['daywind']}风{day['daypower']}级。\n"
            prompt = (
                f"请根据以下天气信息生成简洁友好的回答："
                f"当前天气：{weather}。\n"
                f"未来{n_days}天预报如下：\n{days_text}"
                f"高德API最多只能提供4天预报。"
            )
        else:
            prompt = f"请根据以下天气信息生成简洁友好的回答：{weather}"
        
        try:
            answer = self.ai_service.chatLLM.invoke([HumanMessage(content=prompt)]).content.strip()
            return answer
        except Exception as e:
            # 如果AI调用失败，直接返回天气信息
            if match:
                n_days = int(match.group(1))
                if n_days > 4:
                    n_days = 4
                
                if forecast and "forecasts" in forecast and forecast["forecasts"]:
                    days_data = forecast["forecasts"][0].get("casts", [])[:n_days]
                else:
                    days_data = []
                
                days_text = ""
                for day in days_data:
                    days_text += f"- {day['date']}：{day['dayweather']}，最高{day['daytemp']}℃，最低{day['nighttemp']}℃，{day['daywind']}风{day['daypower']}级。\n"
                
                return f"{weather}\n\n未来{n_days}天预报：\n{days_text}"
            else:
                return f"{weather}"