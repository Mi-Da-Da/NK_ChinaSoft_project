import os

class Config:
    """应用配置类"""
    
    # 高德地图API配置
    AMAP_API_KEY = "a6c590634c3f8ebc42e5037c4ffeea10"
    AMAP_BASE_URL = "https://restapi.amap.com/v3"
    
    # 通义千问API配置
    TONGYI_API_KEY = "sk-02ad1a5086e941c0ae80b541caf3acb0"
    
    # 数据库配置
    DB_URI = "mysql+mysqlconnector://ttt:12345678@10.130.174.186:3306/traval_data"
    
    # Flask应用配置
    DEBUG = True
    HOST = '0.0.0.0'
    PORT = 5000
    
    # 聊天历史文件路径
    HISTORY_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'chat_history.json')
    
    # 城市介绍知识库
    CITY_INTRO_KB = {
        "北京": "北京是中国的首都，拥有悠久的历史和丰富的文化遗产，著名景点包括故宫、长城、颐和园等。",
        "上海": "上海是中国的经济金融中心，兼具现代化都市风貌与历史底蕴，外滩、东方明珠是标志性景点。",
        "西安": "西安是十三朝古都，以兵马俑、大雁塔等历史遗迹闻名，是感受中国古代历史的必访城市。",
        "杭州": "杭州以'上有天堂，下有苏杭'闻名，西湖是核心景点，兼具自然风光与人文底蕴。",
        "成都": "成都是四川省省会，以悠闲的生活节奏、美味的川菜和大熊猫基地闻名。"
    }