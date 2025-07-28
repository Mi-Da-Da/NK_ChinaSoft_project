import requests
import json
import re
from langchain.schema import HumanMessage
from backend.services.ai_service import AIService
from backend.config.settings import Config

class MapService:
    """地图服务类"""
    
    def __init__(self):
        self.ai_service = AIService()
    
    def geocode(self, address):
        """地理编码：将地址转换为坐标"""
        url = f"{Config.AMAP_BASE_URL}/geocode/geo"
        params = {"key": Config.AMAP_API_KEY, "address": address}
        resp = requests.get(url, params=params).json()
        if resp.get("status") == "1" and resp.get("geocodes"):
            return resp["geocodes"][0]["location"]
        # 自动补全"北京市"再查一次
        if not address.startswith("北京"):
            params["address"] = "北京市" + address
            resp = requests.get(url, params=params).json()
            if resp.get("status") == "1" and resp.get("geocodes"):
                return resp["geocodes"][0]["location"]
        return None
    
    def get_city_by_address(self, address):
        """根据地址获取城市"""
        url = f"{Config.AMAP_BASE_URL}/geocode/geo"
        params = {"key": Config.AMAP_API_KEY, "address": address}
        resp = requests.get(url, params=params).json()
        if resp.get("status") == "1" and resp.get("geocodes"):
            return resp["geocodes"][0].get("city")
        return None
    
    def can_use_transit(self, origin_address, dest_address):
        """检查是否可以使用公交"""
        city1 = self.get_city_by_address(origin_address)
        city2 = self.get_city_by_address(dest_address)
        return city1 and city2 and city1 == city2
    
    def get_route(self, origin_addr, dest_addr, mode):
        """获取路线规划"""
        origin = self.geocode(origin_addr) if ',' not in origin_addr else origin_addr
        destination = self.geocode(dest_addr) if ',' not in dest_addr else dest_addr
        if not origin or not destination:
            return {"error": "地址解析失败"}
        
        url = f"{Config.AMAP_BASE_URL}/direction/{mode}"
        params = {"key": Config.AMAP_API_KEY, "origin": origin, "destination": destination}
        if mode == "transit":
            city = self.get_city_by_address(origin_addr)
            if city:
                params["city"] = city
        
        resp = requests.get(url, params=params).json()
        if resp.get("status") != "1":
            return {"error": "高德API请求失败", "raw": resp}
        
        if mode in ["driving", "walking", "riding"]:
            paths = resp.get("route", {}).get("paths", [])
            if not paths:
                return {"error": "未查到可行路线", "raw": resp}
        elif mode == "transit":
            transits = resp.get("route", {}).get("transits", [])
            if not transits:
                return {"error": "未查到可行公交路线", "raw": resp}
        return resp
    
    def extract_travel_mode(self, user_input):
        """提取出行方式"""
        mapping = {
            "快": "driving",
            "最快": "driving",
            "便捷": "driving",
            "方便": "driving",
            "省钱": "transit",
            "经济": "transit",
            "锻炼": "walking",
            "健康": "walking",
            "绿色": "riding",
            "环保": "riding",
            "公交": "transit",
            "地铁": "transit",
            "步行": "walking",
            "骑行": "riding",
            "驾车": "driving",
            "开车": "driving"
        }
        for k, v in mapping.items():
            if k in user_input:
                return v
        
        # 使用AI判断出行方式
        prompt = f"""用户说："{user_input}"，请在["driving", "walking", "riding", "transit"]中选择最合适的出行方式，并只返回英文关键词。"""
        try:
            mode = self.ai_service.chatLLM.invoke([HumanMessage(content=prompt)]).content.strip()
            if mode in ["driving", "walking", "riding", "transit"]:
                return mode
        except:
            pass
        return "driving"  # 默认
    
    def process_search_request(self, user_input):
        """处理地图搜索请求"""
        # 提取搜索关键词
        search_info = self.ai_service.extract_search_keywords(user_input)
        keywords = search_info.get('keywords', [])
        city = search_info.get('city')
        types = search_info.get('types')
        
        if not keywords and not city:
            return "抱歉，我没有找到合适的关键词进行搜索。请提供更具体的地点信息。"
        
        # 构建搜索查询
        search_query = ' '.join(keywords) if keywords else city
        
        # 调用高德地图API
        result = self.search_amap_poi(search_query, city=city, types=types)
        
        if not result or result.get('status') != '1':
            return f"搜索失败，请检查网络连接或API配置。搜索关键词：{search_query}"
        
        # 处理搜索结果
        pois = result.get('pois', [])
        if not pois:
            return f"没有找到与'{search_query}'相关的地点信息。"
        
        # 格式化返回结果
        response = f"找到以下与'{search_query}'相关的地点：\n\n"
        for i, poi in enumerate(pois[:5], 1):  # 只显示前5个结果
            name = poi.get('name', '未知')
            address = poi.get('address', '地址未知')
            distance = poi.get('distance', '距离未知')
            type_name = poi.get('type', '类型未知')
            
            response += f"{i}. {name}\n"
            response += f"   地址：{address}\n"
            response += f"   类型：{type_name}\n"
            if distance != '距离未知':
                response += f"   距离：{distance}米\n"
            response += "\n"
        
        return response
    
    def process_route_request(self, user_input):
        """处理路线规划请求 - 优化起点终点提取逻辑"""
        from backend.services.keyword_service import extract_with_attractions

        # 优先正则提取“从xxx到yyy”或“xxx到yyy”结构
        origin, destination = None, None
        match = re.search(r'从(.+?)到(.+?)(的|怎么|如何|$)', user_input)
        if match:
            origin = match.group(1).strip()
            destination = match.group(2).strip()
        else:
            match2 = re.search(r'(.+?)到(.+?)(的|怎么|如何|$)', user_input)
            if match2:
                origin = match2.group(1).strip()
                destination = match2.group(2).strip()

        # 若正则未命中，fallback到原有逻辑
        if not origin or not destination:
            travel_info = extract_with_attractions(user_input, self.ai_service.chatLLM)
            city = travel_info.get("destination")
            # 解析起点和终点
            if "下车" in user_input and "去" in user_input:
                try:
                    origin = user_input.split("下车")[0].replace("从", "").strip()
                    destination = user_input.split("去")[1].strip()
                except:
                    pass
            elif "从" in user_input and "到" in user_input:
                try:
                    origin = user_input.split("从")[1].split("到")[0].strip()
                    destination = user_input.split("到")[1].split("的")[0].strip()
                except:
                    pass
            elif "去" in user_input:
                destination = user_input.split("去")[1].strip()
                origin = city
            elif "到" in user_input:
                destination = user_input.split("到")[1].strip()
                origin = city
            if not origin:
                origin = city
            if not destination:
                destination = city

        print(f"[ROUTE] origin: {origin}, destination: {destination}")

        if origin and destination and origin != destination:
            mode = self.extract_travel_mode(user_input)
            print(f"[ROUTE] mode: {mode}")
            route_info = self.get_route(origin, destination, mode)
            print(f"[ROUTE] route_info: {route_info}")
            
            if route_info and isinstance(route_info, dict) and route_info.get("error"):
                return f"很抱歉，{route_info.get('error')}。如需帮助请检查输入的地址是否准确，或稍后再试。"
            
            prompt = f"用户需求：{user_input}\n路线信息：{json.dumps(route_info, ensure_ascii=False)}\n请用简洁友好的语气，帮我推荐最优出行方式并说明理由。"
            try:
                answer = self.ai_service.chatLLM.invoke([HumanMessage(content=prompt)]).content.strip()
                answer += "\n\n<em style='color:#888;'>如果您想获取更加细致的路径信息，请在实时助手中进行查询。</em>"
                return answer
            except Exception as e:
                # 如果AI调用失败，返回简化版本
                return f"从{origin}到{destination}的路线规划：\n出行方式：{mode}\n详细信息请查看高德地图。"

        return "请提供明确的起点和终点地址。"
    
    def search_amap_poi(self, keywords, city=None, types=None, page=1, offset=20):
        """搜索高德地图POI（兴趣点）"""
        url = f"{Config.AMAP_BASE_URL}/place/text"
        params = {
            'key': Config.AMAP_API_KEY,
            'keywords': keywords,
            'page': page,
            'offset': offset,
            'output': 'json'
        }
        
        if city:
            params['city'] = city
        if types:
            params['types'] = types
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"⚠️ 高德地图API请求失败：{e}")
            return None