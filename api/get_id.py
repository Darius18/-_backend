from flask import jsonify, make_response, Blueprint, request
from db import get_db_connection  # 假设你有一个数据库连接函数

# 定义一个 Blueprint
get_id_bp = Blueprint('get_id', __name__)

@get_id_bp.route('/api/get_id', methods=['POST'])
def get_id():
    try:
        # 获取请求数据，确保是POST请求并有传递关键字
        data = request.get_json()
        if not data or 'keyword' not in data:
            return make_response(jsonify({'error': 'Missing keyword'}), 400)

        keyword = data['keyword']

        # 获取数据库连接
        conn = get_db_connection()
        cursor = conn.cursor()

        # 判断 keyword 是否为纯数字字符串
        if keyword.isdigit():
            # 如果 keyword 是数字字符串，则查询身份证号字段
            query = "SELECT `身份证号` FROM users WHERE `身份证号` LIKE ? LIMIT 15"
            cursor.execute(query, (f'{keyword}%',))
        else:
            # 如果 keyword 含有非数字字符，则查询姓名字段
            query = "SELECT `姓名` FROM users WHERE `姓名` LIKE ? LIMIT 15"
            cursor.execute(query, (f'{keyword}%',))

        # 获取匹配的结果
        results = cursor.fetchall()

        # 关闭数据库连接
        cursor.close()
        conn.close()

        # 根据查询的字段，返回不同的字段内容
        if keyword.isdigit():
            id_cards = [row['身份证号'] for row in results]
            return jsonify({'matched': id_cards})
        else:
            names = [row['姓名'] for row in results]
            return jsonify({'matched': names})

    except Exception as e:
        # 捕获并返回异常
        return make_response(jsonify({'error': str(e)}), 500)
