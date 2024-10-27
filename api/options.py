from flask import Blueprint, jsonify
from db import get_db_connection
# 定义一个 Blueprint
options_bp = Blueprint('options', __name__)

@options_bp.route('/api/options', methods=['GET'])
def get_options():
    conn = get_db_connection()
    cursor = conn.cursor()

    # 定义要统计的字段
    fields = [
        "BMI类型", "健康分类", "吸烟量", "年龄范围", "建档人", "建档机构", 
        "性别", "慢病分类", "是否吸烟", "是否锻炼", "是否饮酒", 
        "最近就诊时间范围", "服务团队", "社区", "空腹血糖值", 
        "签约团队", "管理机构", "血压类型", "责任医生", 
        "饮酒类型", "饮酒量", "饮酒频率", "饮食习惯类型","queue_status"
    ]

    # 构建 SQL 查询来获取所有字段的值
    query = f"SELECT {', '.join(fields)} FROM users"
    
    cursor.execute(query)
    all_rows = cursor.fetchall()

    result = {field: set() for field in fields}

    # 遍历所有行，将字段的值添加到对应集合，去重
    for row in all_rows:
        for field in fields:
            if row[field] is not None:
                result[field].add(row[field])

    # 将集合转换为列表
    result = {field: list(values) for field, values in result.items()}

    # 手动加入布尔型字段 ['是', '否']，不查表
    boolean_fields = [
        "是否居家", "是否建档", "是否有冠心病", "是否有慢阻肺",
        "是否有糖尿病", "是否有结核病", "是否有脑卒中", 
        "是否有高血压", "是否签约", "是否重点人群"
    ]

    for field in boolean_fields:
        result[field] = ['是', '否']

    # 关闭数据库连接
    conn.close()

    # 返回JSON结果
    return jsonify(result)
