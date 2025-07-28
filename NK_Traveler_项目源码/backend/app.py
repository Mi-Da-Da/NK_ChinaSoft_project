from flask import Flask
from flask_cors import CORS
from backend.config.settings import Config
from backend.api.chat_routes import chat_bp
from backend.api.map_routes import map_bp
from backend.api.session_routes import session_bp
from backend.api.weather_routes import weather_bp

def create_app(config_class=Config):
    """创建Flask应用实例"""
    app = Flask(__name__, 
                template_folder='../frontend/templates',
                static_folder='../frontend/static')
    
    # 加载配置
    app.config.from_object(config_class)
    
    # 注册中间件
    CORS(app)
    
    # 注册蓝图 - 保持原来的访问地址
    app.register_blueprint(chat_bp, url_prefix='/')  # 主页在根路径
    app.register_blueprint(map_bp, url_prefix='/amap')  # 地图API保持原路径
    app.register_blueprint(session_bp, url_prefix='')  # 会话管理在根路径
    app.register_blueprint(weather_bp, url_prefix='')  # 天气API在根路径
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=Config.DEBUG, host=Config.HOST, port=Config.PORT)