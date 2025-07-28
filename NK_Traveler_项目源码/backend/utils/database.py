from langchain_community.utilities import SQLDatabase
from backend.config.settings import Config

def get_database():
    """获取数据库连接"""
    return SQLDatabase.from_uri(Config.DB_URI)

def get_usable_tables():
    """获取可用的数据库表"""
    db = get_database()
    return db.get_usable_table_names()