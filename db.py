# # db.py
# import sqlite3

# def get_db_connection():
#     """Connects to the SQLite database."""
#     # connection = sqlite3.connect('medical_users.db')
#     connection = sqlite3.connect('/root/sdb1/taihang0816/home/database.db')
#     connection.row_factory = sqlite3.Row  # This allows us to access columns by name
#     return connection


# db.py
import sqlite3
import os  # 用于获取环境变量

def get_db_connection():
    """Connects to the SQLite database."""
    # 读取环境变量，选择不同的数据库
    environment = os.getenv('FLASK_ENV', 'development')  # 默认为开发环境

    if environment == 'production':
        db_path = '/root/sdb1/taihang0816/home/database.db'
    else:
        db_path = 'medical_users.db'

    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row  # This allows us to access columns by name
    return connection
