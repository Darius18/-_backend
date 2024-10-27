# app.py
from flask import Flask
from flask_cors import CORS  # 导入 CORS
from api.chart_left_right import chart_bp  # 导入 Blueprint
from api.options import options_bp  # 导入 Blueprint
from api.filter import filter_bp  # 导入 Blueprint
from api.map import map_bp  # 导入 Blueprint
from api.get_id import get_id_bp  # 导入 Blueprint
import os  # 用于获取环境变量

app = Flask(__name__)
CORS(app)  # 允许所有的跨域请求

# 注册 Blueprint
app.register_blueprint(chart_bp)
app.register_blueprint(options_bp)
app.register_blueprint(filter_bp)
app.register_blueprint(map_bp)
app.register_blueprint(get_id_bp)

if __name__ == '__main__':
    # 通过环境变量控制端口和调试模式
    environment = os.getenv('FLASK_ENV', 'development')
    print(f"FLASK_ENV is set to: {environment}", flush=True)
    
    if environment == 'production':
        port = 5002
        debug = True
    else:
        port = 5001
        debug = True

    app.run(debug=debug, host='0.0.0.0', port=port)
