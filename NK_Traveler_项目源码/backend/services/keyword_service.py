import re
from backend.services.ai_service import AIService

def regex_fallback(user_input):
    """正则表达式回退方案 - 提取旅游相关信息"""
    fallback = {
        "destination": None, "days": 2, "interests": [], "style": "适中", "attractions": []
    }
    
    # 提取城市名
    city_patterns = [r'去(.*?)玩', r'到(.*?)旅游', r'(.*?)旅游', r'(.*?)的行程']
    for pattern in city_patterns:
        match = re.search(pattern, user_input)
        if match:
            for group in match.groups():
                if group and len(group) > 1 and not group.isdigit():
                    fallback["destination"] = group.strip()
                    break
        if fallback["destination"]:
            break
    
    # 提取天数
    day_match = re.search(r'(\d+)天', user_input)
    if day_match:
        fallback["days"] = int(day_match.group(1))
    
    # 提取兴趣类型
    interest_map = {
        "历史": ["历史", "古迹", "博物馆"],
        "自然": ["自然", "风景", "山水"],
        "美食": ["美食", "吃", "小吃"],
        "购物": ["购物", "商场"]
    }
    for interest, keywords in interest_map.items():
        for kw in keywords:
            if kw in user_input and interest not in fallback["interests"]:
                fallback["interests"].append(interest)
    if not fallback["interests"]:
        fallback["interests"].append("综合")
    
    # 提取行程风格
    if any(kw in user_input for kw in ["轻松", "不要太累", "休闲"]):
        fallback["style"] = "休闲"
    elif any(kw in user_input for kw in ["紧凑", "快", "赶"]):
        fallback["style"] = "紧凑"
    
    # 提取景点信息
    known_attractions = {"故宫": "北京", "长城": "北京", "兵马俑": "西安", "西湖": "杭州", "外滩": "上海"}
    for attr, city in known_attractions.items():
        if attr in user_input:
            fallback["attractions"].append(attr)
            if not fallback["destination"]:
                fallback["destination"] = city
    
    return fallback

def extract_with_attractions(user_input, chatLLM, max_retries=2):
    """提取旅游相关信息 - 使用AI服务"""
    # 创建AI服务实例
    ai_service = AIService()
    
    prompt = f'''
    提取以下5个字段为JSON：
    1. destination：城市名（如"北京"）
    2. days：整数天数（如2）
    3. interests：兴趣列表（如["历史"]）
    4. style："紧凑"/"适中"/"休闲"
    5. attractions：景点列表（如["故宫"]）
    示例：输入"看兵马俑，玩2天，不要太累" → {{"destination": "西安", "days": 2, "interests": ["历史"], "style": "休闲", "attractions": ["兵马俑"]}}
    用户输入：{user_input}
    '''
    
    # 使用AI服务的通用方法
    result = ai_service.extract_json_from_ai(
        prompt, 
        required_fields=["destination", "days", "interests", "style", "attractions"],
        max_retries=max_retries
    )
    
    if result:
        return result
    
    # AI失败时使用正则回退
    return regex_fallback(user_input)