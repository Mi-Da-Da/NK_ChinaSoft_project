import json
import re
from langchain.schema import HumanMessage
from langchain_community.chat_models.tongyi import ChatTongyi
from backend.config.settings import Config

class AIService:
    """AI服务类 - 核心AI模型和通用提取功能"""
    
    def __init__(self):
        self.chatLLM = ChatTongyi(
            streaming=False,
            dashscope_api_key=Config.TONGYI_API_KEY
        )
    
    def invoke_ai(self, prompt, max_retries=2):
        """通用AI调用方法"""
        for retry in range(max_retries):
            try:
                response = self.chatLLM.invoke([HumanMessage(content=prompt)])
                return response.content.strip()
            except Exception as e:
                print(f"⚠️ AI调用失败（{e}），重试第{retry + 1}次")
                if retry < max_retries - 1:
                    import time
                    time.sleep(1)
        return None
    
    def extract_json_from_ai(self, prompt, required_fields=None, max_retries=2):
        """从AI响应中提取JSON数据"""
        response = self.invoke_ai(prompt, max_retries)
        if not response:
            return None
        
        try:
            # 清理响应中的markdown代码块
            info_str = response.replace("```json", "").replace("```", "").strip()
            result = json.loads(info_str)
            
            # 验证必需字段
            if required_fields and not all(field in result for field in required_fields):
                return None
                
            return result
        except Exception as e:
            print(f"⚠️ JSON解析失败：{e}")
            return None
    
    def extract_search_keywords(self, user_input):
        """从用户输入中提取用于高德地图搜索的关键词"""
        prompt = f"""
        从以下用户输入中提取用于地图搜索的关键词，返回JSON格式：
        1. 景点名称（如：故宫、长城、西湖等）
        2. 地点类型（如：博物馆、公园、餐厅、酒店等）
        3. 城市名称（如：北京、上海等）
        4. 具体地址或区域（如：天安门广场、外滩等）
        
        返回格式：{{"keywords": ["关键词1", "关键词2"], "city": "城市名", "types": "POI类型"}}
        
        用户输入：{user_input}
        """
        
        result = self.extract_json_from_ai(prompt, ["keywords", "city"])
        if result:
            return result
        
        # 回退到正则表达式提取
        return self.regex_extract_keywords(user_input)
    
    def regex_extract_keywords(self, user_input):
        """使用正则表达式提取关键词（回退方案）"""
        keywords = []
        city = None
        types = None
        
        # 提取城市名
        city_patterns = [r'去(.*?)玩', r'到(.*?)旅游', r'(.*?)旅游', r'在(.*?)的', r'(.*?)有什么']
        for pattern in city_patterns:
            match = re.search(pattern, user_input)
            if match:
                city = match.group(1).strip()
                break
        
        # 提取景点名称
        attraction_patterns = [
            r'故宫', r'长城', r'兵马俑', r'西湖', r'外滩', r'天安门', r'颐和园', r'圆明园',
            r'大雁塔', r'钟楼', r'鼓楼', r'南锣鼓巷', r'王府井', r'三里屯', r'鸟巢', r'水立方'
        ]
        for pattern in attraction_patterns:
            if pattern in user_input:
                keywords.append(pattern)
        
        return {
            "keywords": keywords,
            "city": city,
            "types": types
        }
    
    def process_general_request(self, user_input):
        """处理一般性请求"""
        return "AI服务正在处理您的请求..."
        