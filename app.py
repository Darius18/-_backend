from flask import Flask
from api.chart_left_right import chart_bp  # 导入 Blueprint
from api.options import options_bp  # 导入 Blueprint
from api.filter import filter_bp  # 导入 Blueprint

app = Flask(__name__)

# 注册 Blueprint
app.register_blueprint(chart_bp)
app.register_blueprint(options_bp)
app.register_blueprint(filter_bp)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
