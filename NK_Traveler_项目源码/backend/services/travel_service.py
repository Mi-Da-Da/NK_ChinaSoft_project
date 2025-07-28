import re
import json
import time
from langchain.schema import HumanMessage
from backend.services.ai_service import AIService
from backend.services.search_service import SearchService
from backend.services.keyword_service import extract_with_attractions
from backend.config.settings import Config


class TravelService:
    def __init__(self, search_service):
        self.ai_service = AIService()
        self.search_service = search_service

    def parse_multi_city(self, user_input):
        """解析用户输入中的多城市行程"""
        patterns = [
            r'先去(.*?)玩(\d+)天，再去(.*?)玩(\d+)天',
            r'(.*?)玩(\d+)天，然后(.*?)玩(\d+)天',
            r'去(.*?)(\d+)天，(.*?)(\d+)天'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, user_input)
            if match and len(match.groups()) == 4:
                city1, day1, city2, day2 = match.groups()
                return [(city1.strip(), int(day1)), (city2.strip(), int(day2))], int(day1) + int(day2)
        
        # 单城市情况
        travel_info = extract_with_attractions(user_input, self.ai_service.chatLLM)
        city = travel_info.get("destination") or "未知"
        days = travel_info.get("days", 2)
        return [(city, days)], days
    
    def extract_travel_params(self, user_input):
        """从用户输入提取行程关键参数（支持多城市）"""
        cities_with_days, total_days = self.parse_multi_city(user_input)
        
        params = {
            "departure": "未知",
            "cities": cities_with_days,
            "total_days": total_days,
            "style": "适中",
            "budget": 5000,
            "people": 1,
            "preferences": ""
        }
        
        # 提取出发地
        departure_patterns = [r'从(.*?)出发', r'从(.*?)去', r'从(.*?)到']
        for pattern in departure_patterns:
            match = re.search(pattern, user_input)
            if match and match.group(1):
                params["departure"] = match.group(1).strip()
                break
        
        # 提取预算
        budget_match = re.search(r'预算(\d+)元', user_input)
        if budget_match:
            params["budget"] = int(budget_match.group(1))
        
        # 提取随行人数
        people_match = re.search(r'(\d+)人', user_input)
        if people_match:
            params["people"] = int(people_match.group(1))
        
        # 提取行程风格
        if any(kw in user_input for kw in ["轻松", "不要太累", "休闲"]):
            params["style"] = "休闲"
        elif any(kw in user_input for kw in ["紧凑", "快", "赶"]):
            params["style"] = "紧凑"
        
        # 提取偏好
        travel_info = extract_with_attractions(user_input, self.ai_service.chatLLM)
        params["preferences"] = f"感兴趣景点：{','.join(travel_info.get('attractions', []))}"
        
        return params
    
    def need_travel_plan(self, user_input):
        """判断用户是否需要生成行程表"""
        plan_keywords = ["行程", "计划", "安排", "攻略", "路线"]
        return any(kw in user_input for kw in plan_keywords)
    
    def generate_multi_city_plan(self, params, search=False):
        """生成多城市连续行程表"""
        all_cities_plan = []
        current_day = 1
        
        for city, days_in_city in params["cities"]:
            # 获取景点信息
            attractions = self.get_city_attractions(city)
            
            # 获取实时信息（仅在search为True时联网）
            realtime_info = {}
            if search and self.search_service.is_search_enabled():
                realtime_info = self.search_service.get_realtime_travel_info(city, days_in_city, attractions)
                print(f"🔍 为{city}获取实时信息")
            else:
                print(f"⏩ 跳过{city}的实时信息获取（未开启联网搜索）")
            
            # 生成该城市的行程
            city_plan = self.generate_single_city_plan(
                params["departure"], city, days_in_city, params["style"], 
                params["budget"], params["people"], params["preferences"], 
                attractions, realtime_info
            )
            all_cities_plan.append(city_plan)
            current_day += days_in_city
        
        # 合并行程表
        return self.merge_plans(all_cities_plan)
    
    def get_city_attractions(self, city):
        """获取城市景点信息 - 支持数据库查询"""
        if not city:
            return []
        
        # 尝试从数据库查询（保留接口，暂时使用默认数据）
        try:
            # 这里可以添加数据库查询逻辑
            # from backend.utils.database import get_database
            # db = get_database()
            # query = f"SELECT name, introduce FROM tourist_attraction_data WHERE city = '{city}' LIMIT 5;"
            # results = db.run(query)
            # attractions = []
            # if results:
            #     lines = results.strip().split('\n')
            #     for line in lines:
            #         if ',' in line:
            #             parts = line.split(',', 1)
            #             if len(parts) == 2:
            #                 name, intro = parts
            #                 attractions.append({"name": name.strip(), "introduce": intro.strip()})
            # return attractions
            pass
        except Exception as e:
            print(f"⚠️ 数据库查询失败，使用默认数据：{e}")
        
        # 使用默认数据
        default_attractions = {
            "北京": [
                {"name": "故宫", "introduce": "明清两代皇宫，世界文化遗产"},
                {"name": "长城", "introduce": "万里长城，中华民族的象征"},
                {"name": "天安门广场", "introduce": "世界最大的城市广场"}
            ],
            "杭州": [
                {"name": "西湖", "introduce": "人间天堂，诗画江南"},
                {"name": "灵隐寺", "introduce": "千年古刹，禅意悠远"},
                {"name": "雷峰塔", "introduce": "白娘子传说，西湖十景"}
            ],
            "上海": [
                {"name": "外滩", "introduce": "万国建筑博览，黄浦江畔"},
                {"name": "东方明珠", "introduce": "上海地标，陆家嘴风光"},
                {"name": "豫园", "introduce": "江南园林，老上海风情"}
            ],
            "西安": [
                {"name": "兵马俑", "introduce": "世界第八大奇迹，秦始皇陵墓"},
                {"name": "大雁塔", "introduce": "唐代佛教建筑，玄奘法师藏经处"},
                {"name": "华清池", "introduce": "唐代皇家园林，杨贵妃沐浴地"}
            ],
            "成都": [
                {"name": "大熊猫基地", "introduce": "国宝大熊猫繁育研究基地"},
                {"name": "宽窄巷子", "introduce": "清代古街区，成都文化缩影"},
                {"name": "都江堰", "introduce": "世界文化遗产，古代水利工程"}
            ]
        }
        return default_attractions.get(city, [
            {"name": "主要景点", "introduce": f"{city}的主要旅游景点"},
            {"name": "文化古迹", "introduce": f"{city}的历史文化遗迹"},
            {"name": "自然风光", "introduce": f"{city}的自然景观"}
        ])
    
    def generate_single_city_plan(self, departure, city, days, style, budget, people, preferences, attractions, realtime_info):
        """生成单城市行程 - 使用详细的提示词工程"""
        # 格式化景点信息（含门票/开放时间）
        attractions_str = ""
        for idx, attr in enumerate(attractions):
            details = attr.get("details", {})
            extra = []
            if details.get("ticket"):
                extra.append(f"门票：{details['ticket'].split('-')[-1].strip()}")  # 提取关键信息
            if details.get("opening_hours"):
                extra.append(f"开放时间：{details['opening_hours'].split('-')[-1].strip()}")
            attractions_str += f"- {attr['name']}：{attr['introduce'][:50]}... {'；'.join(extra)}\n"

        # 格式化实时信息
        realtime_str = ""
        if realtime_info:
            realtime_str = "\n".join([
                f"{k}：{v}" for k, v in realtime_info.items() 
                if "未找到" not in v and "不可用" not in v
            ])
        
        # 如果没有实时信息，添加说明
        if not realtime_str:
            realtime_str = "（实时搜索功能已禁用，使用基础信息生成行程）"

        # 详细的AI提示词工程
        prompt = """你现在是一位专业的旅行规划师，你的责任是根据旅行出发地、目的地、天数、行程风格（紧凑、适中、休闲）、预算、随行人数，帮助我规划旅游行程并生成详细的旅行计划表。需生成单城市行程并衔接前后城市，请你以表格的方式呈现结果。旅行计划表的表头请包含日期、地点、行程计划、交通方式、餐饮安排、住宿安排、费用估算、备注。所有表头都为必填项，请加深思考过程，实时信息需融入行程：严格遵守以下规则：

1. 日期请以DayN为格式如Day1，明确标识每天的行程。
2. 地点需要呈现当天所在城市，请根据日期、考虑地点的地理位置远近，严格且合理制定地点，确保行程顺畅。
3. 行程计划需包含位置、时间、活动，其中位置需要根据地理位置的远近进行排序。位置的数量可以根据行程风格灵活调整，如休闲则位置数量较少、紧凑则位置数量较多。时间需要按照上午、中午、晚上制定，并给出每一个位置所停留的时间（如上午10点-中午12点）。活动需要准确描述在位置发生的对应活动（如参观博物馆、游览公园、吃饭等），并需根据位置停留时间合理安排活动类型。
4. 交通方式需根据地点、行程计划中的每个位置的地理距离合理选择，如步行、地铁、出租车、火车、飞机等不同的交通方式，并尽可能详细说明。
5. 餐饮安排需包含每餐的推荐餐厅、类型（如本地特色、快餐等）、预算范围，就近选择。
6. 住宿安排需包含每晚的推荐酒店或住宿类型（如酒店、民宿等）、地址、预估费用，就近选择。
7. 费用估算需包含每天的预估总费用，并注明各项费用的细分（如交通费、餐饮费、门票费等）。
8. 备注中需要包括对应行程计划需要考虑到的注意事项，保持多样性，涉及饮食、文化、天气、语言等方面的提醒。
9. 请特别考虑随行人数的信息，确保行程和住宿安排能满足所有随行人员的需求。
10.旅游总体费用不能超过预算。
11.若有下一个城市，最后一天需包含前往下一个城市的交通安排（如高铁/飞机）。
12.行程表表头：日期、地点、行程计划、交通方式、餐饮安排、住宿安排、费用估算、备注。
13.行程计划中需体现景点的开放时间（如"上午9:00-11:30：参观故宫（开放时间9:00-17:00）"）。
14.费用估算需包含门票（若有），无门票则不显示。

现在请你严格遵守以上规则，根据我的旅行出发地、目的地、天数、行程风格（紧凑、适中、休闲）、预算、随行人数，生成合理且详细的旅行计划表。记住你要根据我提供的旅行目的地、天数等信息以表格形式生成旅行计划表，最终答案一定是表格形式。以下是旅行的基本信息：
旅游出发地：{departure}，旅游目的地：{city} ，天数：{days_in_city}天 ，行程风格：{style} ，预算：{budget}元，随行人数：{people}人, 特殊偏好、要求：{preferences}

可参考的当地景点：
{attractions_str}

实时参考信息（请融入行程）：
{realtime_str}
""".format(
            departure=departure,
            city=city,
            days_in_city=days,
            style=style,
            budget=budget,
            people=people,
            preferences=preferences,
            attractions_str=attractions_str,
            realtime_str=realtime_str
        )

        try:
            response = self.ai_service.chatLLM.invoke([HumanMessage(content=prompt)])
            city_plan = response.content.strip().replace("```markdown", "").replace("```", "")
            return city_plan
        except Exception as e:
            print(f"⚠️ {city}行程生成失败：{e}")
            return f"### {city}行程生成失败"
    
    def merge_plans(self, plans):
        """合并多个城市的行程表"""
        full_plan = "\n".join(plans)
        # 去重表头
        lines = full_plan.split('\n')
        header = None
        cleaned_lines = []
        for line in lines:
            if "| 日期 | 地点 | 行程计划 |" in line and not header:
                header = line
                cleaned_lines.append(line)
            elif "| 日期 | 地点 | 行程计划 |" in line:
                continue
            else:
                cleaned_lines.append(line)
        return "\n".join(cleaned_lines)
    
    def generate_travel_plan(self, departure, destination, days, style, budget, people, preferences):
        """生成旅游计划 - 兼容原有接口"""
        # 检查是否是多城市
        if "先去" in preferences or "然后" in preferences:
            params = {
                "departure": departure,
                "cities": [(destination, days)],
                "total_days": days,
                "style": style,
                "budget": budget,
                "people": people,
                "preferences": preferences
            }
            return self.generate_multi_city_plan(params)
        
        # 单城市情况
        attractions = self.get_city_attractions(destination)
        realtime_info = {}
        if self.search_service.is_search_enabled():
            realtime_info = self.search_service.get_realtime_travel_info(destination, days, attractions)
        return self.generate_single_city_plan(
            departure, destination, days, style, budget, people, preferences, 
            attractions, realtime_info
        )