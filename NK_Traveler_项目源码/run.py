 #!/usr/bin/env python3
"""
NK-Traveler 智能旅游攻略定制系统
主启动脚本
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.app import create_app

if __name__ == '__main__':
    app = create_app()
    print("🚀 启动 NK-Traveler 智能旅游攻略定制系统...")
    print(f"📍 访问地址: http://{app.config['HOST']}:{app.config['PORT']}")
    app.run(debug=app.config['DEBUG'], host=app.config['HOST'], port=app.config['PORT'])
    