from flask import Flask
from flask_cors import CORS  # 导入 CORS
from api.chart_left_right import chart_bp  # 导入 Blueprint
from api.options import options_bp  # 导入 Blueprint
from api.filter import filter_bp  # 导入 Blueprint
from api.map import map_bp  # 导入 Blueprint

app = Flask(__name__)
CORS(app)  # 允许所有的跨域请求

# 注册 Blueprint
app.register_blueprint(chart_bp)
app.register_blueprint(options_bp)
app.register_blueprint(filter_bp)
app.register_blueprint(map_bp)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
