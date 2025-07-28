import json
import re
from langchain.schema import HumanMessage
from backend.services.ai_service import AIService
from backend.services.travel_service import TravelService
from backend.services.weather_service import WeatherService
from backend.services.map_service import MapService
from backend.services.keyword_service import extract_with_attractions
from backend.services.search_service import SearchService
from backend.config.settings import Config
from ddgs import DDGS
from backend.services.attractions_service import AttractionsService


class ChatService:
    """聊天服务类 - 增强版，支持智能判断和实时信息"""

    def __init__(self, search_service):
        self.search_service = search_service
        self.ai_service = AIService()
        self.travel_service = TravelService(search_service)
        self.weather_service = WeatherService()
        self.map_service = MapService()
        self.attractions_service = AttractionsService()  # 新增RAG增强服务

    def process_message(self, user_input, search=False, rag=False):
        print(f"🤖 处理用户消息：{user_input}")

        # RAG增强优先分流
        if rag:
            print("🧠 RAG增强分支")
            rag_result = self.attractions_service.query(user_input)
            if isinstance(rag_result, dict) and "answer" in rag_result:
                answer = rag_result["answer"]
                # 可选：附加来源信息
                if rag_result.get("sources"):
                    answer += "\n\n【参考资料】\n" + "\n".join([f"- {src['source']}: {src['content']}" for src in rag_result["sources"]])
                return answer
            else:
                return rag_result.get("error", "RAG增强服务异常")

        # 行程规划关键词优先分流（顺序提前，必须在路径规划正则分流之前）
        travel_plan_keywords = ["行程", "规划", "计划", "安排", "攻略", "旅游", "路线推荐", "详细日程"]
        if any(kw in user_input for kw in travel_plan_keywords):
            print("📋 触发行程规划分支")
            params = self.travel_service.extract_travel_params(user_input)
            valid_cities = [(c, d) for c, d in params["cities"] if c and c != "未知" and d > 0]
            if not valid_cities:
                return "请明确旅行目的地及停留天数，以便为你规划行程（例如：先去杭州玩2天，再去上海玩1天）。"
            params["cities"] = valid_cities
            return self.travel_service.generate_multi_city_plan(params, search=search)

        # 路径规划正则优先分流
        if re.search(r'从.+到.+', user_input) or re.search(r'.+到.+', user_input) or re.search(r'.+去.+', user_input):
            print("🗺️ 触发主聊天路径规划正则分支")
            return self.map_service.process_route_request(user_input)

        # 路径规划关键词优先分流
        route_keywords = [
            "怎么去", "路线", "出行", "最快", "便捷", "公交", "地铁", "驾车", "步行", "骑行",
            "下车", "如何到", "如何去", "怎么到"
        ]
        if any(kw in user_input for kw in route_keywords):
            print("🗺️ 触发主聊天路径规划分支")
            return self.map_service.process_route_request(user_input)

        # 天气分流
        if "天气" in user_input:
            print("🌤️ 触发主聊天天气查询分支")
            answer = self.weather_service.process_weather_request(user_input)
            answer += "\n\n<em style='color:#888;'>如果您想了解更加详细的天气信息，请在实时助手中进行查询。</em>"
            return answer

        # 联网搜索实时信息分流（仅在search=True时生效，且优先级低于行程、路径、天气）
        if search:
            realtime_keywords = [
                "门票", "开放时间", "营业时间", "预约", "票价", "价格", "限流", "交通", "实时", "最新", "政策", "高铁", "地铁", "公交", "交通管制",
                "预约政策", "入园要求", "检票", "购票", "临时关闭", "暂停开放", "疫情", "高峰期", "人流量", "交通状况", "突发事件"
            ]
            if any(kw in user_input for kw in realtime_keywords):
                print("🔍 触发联网实时信息搜索分支")
                result = self.search_service.search_internet(user_input)
                if result and "未找到" not in result:
                    return result
                # 联网失败时兜底
            print("🏛️ 处理常规旅游咨询（联网兜底）")
            # 兜底本地知识
            travel_info = extract_with_attractions(user_input, self.ai_service.chatLLM)
            city = travel_info.get("destination")
            days = travel_info.get("days", 2)
            style = travel_info.get("style", "适中")
            interests = travel_info.get("interests", [])
            attractions = travel_info.get("attractions", [])
            if not interests:
                interests = ["综合"]
            city_intro = self.get_city_introduction(city) if city else "未明确旅行目的地"
            response = f"{city_intro}\n"
            if attractions:
                response += f"你提到的景点：{', '.join(attractions)}\n"
            else:
                response += "可以告诉我更多偏好，为你推荐合适的景点～\n"
            response += f"根据你的需求，建议安排{days}天{style}行程，适合体验{', '.join(interests)}相关的活动。"
            return response
        else:
            # 本地AI提示词生成行程表（不依赖 travel_service，完全本地）
            # 1. 解析参数
            travel_info = extract_with_attractions(user_input, self.ai_service.chatLLM)
            city = travel_info.get("destination") or "未知"
            days = travel_info.get("days", 2)
            style = travel_info.get("style", "适中")
            interests = travel_info.get("interests", [])
            attractions = travel_info.get("attractions", [])
            budget = 5000
            people = 1
            preferences = f"感兴趣景点：{','.join(attractions)}"
            # 2. 构造景点字符串
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
            attractions_list = default_attractions.get(city, [
                {"name": "主要景点", "introduce": f"{city}的主要旅游景点"},
                {"name": "文化古迹", "introduce": f"{city}的历史文化遗迹"},
                {"name": "自然风光", "introduce": f"{city}的自然景观"}
            ])
            attractions_str = ""
            for attr in attractions_list:
                attractions_str += f"- {attr['name']}：{attr['introduce'][:50]}...\n"
            # 3. 构造提示词
            prompt = f"""你现在是一位专业的旅行规划师，你的责任是根据旅行出发地、目的地、天数、行程风格（紧凑、适中、休闲）、预算、随行人数，帮助我规划旅游行程并生成详细的旅行计划表。需生成单城市行程并衔接前后城市，请你以表格的方式呈现结果。旅行计划表的表头请包含日期、地点、行程计划、交通方式、餐饮安排、住宿安排、费用估算、备注。所有表头都为必填项，请加深思考过程，实时信息需融入行程：严格遵守以下规则：\n\n1. 日期请以DayN为格式如Day1，明确标识每天的行程。\n2. 地点需要呈现当天所在城市，请根据日期、考虑地点的地理位置远近，严格且合理制定地点，确保行程顺畅。\n3. 行程计划需包含位置、时间、活动，其中位置需要根据地理位置的远近进行排序。位置的数量可以根据行程风格灵活调整，如休闲则位置数量较少、紧凑则位置数量较多。时间需要按照上午、中午、晚上制定，并给出每一个位置所停留的时间（如上午10点-中午12点）。活动需要准确描述在位置发生的对应活动（如参观博物馆、游览公园、吃饭等），并需根据位置停留时间合理安排活动类型。\n4. 交通方式需根据地点、行程计划中的每个位置的地理距离合理选择，如步行、地铁、出租车、火车、飞机等不同的交通方式，并尽可能详细说明。\n5. 餐饮安排需包含每餐的推荐餐厅、类型（如本地特色、快餐等）、预算范围，就近选择。\n6. 住宿安排需包含每晚的推荐酒店或住宿类型（如酒店、民宿等）、地址、预估费用，就近选择。\n7. 费用估算需包含每天的预估总费用，并注明各项费用的细分（如交通费、餐饮费、门票费等）。\n8. 备注中需要包括对应行程计划需要考虑到的注意事项，保持多样性，涉及饮食、文化、天气、语言等方面的提醒。\n9. 请特别考虑随行人数的信息，确保行程和住宿安排能满足所有随行人员的需求。\n10.旅游总体费用不能超过预算。\n11.若有下一个城市，最后一天需包含前往下一个城市的交通安排（如高铁/飞机）。\n12.行程表表头：日期、地点、行程计划、交通方式、餐饮安排、住宿安排、费用估算、备注。\n13.行程计划中需体现景点的开放时间（如\"上午9:00-11:30：参观故宫（开放时间9:00-17:00）\"）。\n14.费用估算需包含门票（若有），无门票则不显示。\n\n现在请你严格遵守以上规则，根据我的旅行出发地、目的地、天数、行程风格（紧凑、适中、休闲）、预算、随行人数，生成合理且详细的旅行计划表。记住你要根据我提供的旅行目的地、天数等信息以表格形式生成旅行计划表，最终答案一定是表格形式。以下是旅行的基本信息：\n旅游出发地：未知，旅游目的地：{city} ，天数：{days}天 ，行程风格：{style} ，预算：{budget}元，随行人数：{people}人, 特殊偏好、要求：{preferences}\n\n可参考的当地景点：\n{attractions_str}\n\n实时参考信息（请融入行程）：\n（实时搜索功能已禁用，使用基础信息生成行程）\n"""
            response = self.ai_service.chatLLM.invoke([HumanMessage(content=prompt)])
            city_plan = response.content.strip().replace("```markdown", "").replace("```", "")
            return city_plan

    def get_city_introduction(self, city):
        """获取城市介绍"""
        if not city:
            return "未明确旅行目的地"
        
        if city in Config.CITY_INTRO_KB:
            return Config.CITY_INTRO_KB[city]
        
        return f"{city}是一座值得探索的城市。"
        