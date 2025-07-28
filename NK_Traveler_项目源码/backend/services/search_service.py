import time

class SearchService:
    """联网搜索服务 - 获取实时信息"""

    def __init__(self):
        self.search_available = False
        self.user_enabled_search = True  # 用户是否启用实时搜索
        try:
            from ddgs import DDGS
            self.DDGS = DDGS
            self.search_available = True
        except ImportError:
            print("⚠️ duckduckgo-search 未安装，联网搜索功能不可用")
    
    def set_search_enabled(self, enabled):
        """设置用户是否启用实时搜索"""
        self.user_enabled_search = enabled
        print(f"🔧 用户{'启用' if enabled else '禁用'}了实时搜索功能")
    
    def is_search_enabled(self):
        """检查是否启用实时搜索"""
        return self.search_available and self.user_enabled_search

    def search_internet(self, query, limit=3, timeout=15, max_retries=3):
        """多重试+超时控制的联网搜索，确保实时信息获取"""
        if not self.is_search_enabled():
            return "实时搜索功能已禁用，如需启用请点击设置按钮"

        print(f"🔍 开始搜索：{query}")
        for retry in range(max_retries):
            try:
                with self.DDGS(timeout=timeout) as ddgs:
                    results = list(ddgs.text(query, max_results=limit))
                    if results:
                        result_text = "\n".join([
                            f"- {res['body'][:200]}..."
                            for res in results
                            if res.get('body')
                        ])
                        print(f"✅ 搜索成功：{query}")
                        return result_text
                print(f"⚠️ 未找到结果：{query}")
                return "未找到相关信息。"
            except Exception as e:
                print(f"⚠️ 搜索重试第{retry+1}次失败：{str(e)}")
                if retry < max_retries - 1:
                    time.sleep(1.5)  # 指数退避重试
        print(f"❌ 搜索最终失败：{query}")
        return "搜索服务暂时不可用，部分信息可能滞后。"

    def get_attraction_details(self, attraction_name, city):
        """获取单个景点的门票价格和开放时间"""
        if not self.is_search_enabled():
            return {"ticket": None, "opening_hours": None}

        details = {"ticket": None, "opening_hours": None}

        # 查询门票价格
        ticket_query = f"{attraction_name} {city} 门票价格 2025"
        ticket_info = self.search_internet(ticket_query, limit=1)
        if "未找到" not in ticket_info and "不可用" not in ticket_info:
            details["ticket"] = ticket_info

        # 查询开放时间
        time_query = f"{attraction_name} {city} 开放时间 2025年7月"
        time_info = self.search_internet(time_query, limit=1)
        if "未找到" not in time_info and "不可用" not in time_info:
            details["opening_hours"] = time_info

        return details

    def get_realtime_travel_info(self, destination, days, attractions):
        """获取影响行程的关键实时信息"""
        if not self.is_search_enabled():
            return {}

        realtime_data = {}

        # 未来天气
        weather_query = f"{destination} 未来{days}天天气 2025"
        realtime_data["weather"] = self.search_internet(weather_query, limit=1)

        # 景点详细信息
        if attractions:
            for idx, attr in enumerate(attractions[:3]):
                details = self.get_attraction_details(attr["name"], destination)
                realtime_data[f"attr_{idx}_ticket"] = details["ticket"]
                realtime_data[f"attr_{idx}_time"] = details["opening_hours"]

        # 交通状况
        traffic_query = f"{destination} 景区间交通方式 2025"
        realtime_data["traffic"] = self.search_internet(traffic_query, limit=1)

        return realtime_data

    def need_internet_search(self, user_input):
        """判断用户输入是否涉及实时信息"""
        realtime_keywords = [
            "天气", "开放时间", "今天", "明天", "现在",
            "最新", "门票预约", "交通管制", "路况", "疫情"
        ]
        return any(kw in user_input for kw in realtime_keywords)