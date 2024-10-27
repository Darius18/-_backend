from flask import jsonify, make_response, Blueprint, request
from datetime import datetime
from db import get_db_connection

# 定义一个 Blueprint
filter_bp = Blueprint('filter', __name__)

@filter_bp.route('/api/filter', methods=['POST'])
def filter_users():
    # 获取前端传来的 JSON 数据
    filter_data = request.json
    
    # 构建查询语句的过滤条件
    filters = []
    params = []
    
    # 动态构建查询条件
    for key, value in filter_data.items():
        print(key, value, type(value), isinstance(value, list), flush=True)
        
        # 处理 "最近一次就诊时间" 字段
        if key == "最近一次就诊时间" and isinstance(value, str):
            try:
                date_range = value.split('-')
                if len(date_range) == 2:
                    start_time = datetime.strptime(date_range[0].strip(), "%Y/%m/%d").strftime("%Y-%m-%d")
                    end_time = datetime.strptime(date_range[1].strip(), "%Y/%m/%d").strftime("%Y-%m-%d")
                    filters.append("最近一次就诊时间 BETWEEN ? AND ?")
                    params.append(start_time)
                    params.append(end_time)
                else:
                    return make_response(jsonify({"error": "Invalid date range format"}), 400)
            except ValueError:
                return make_response(jsonify({"error": "Invalid date format"}), 400)

        # 处理身份证号数组
        elif key == "身份证号" and isinstance(value, list) and value:
            placeholders = ', '.join(['?'] * len(value))  # 动态生成占位符
            filters.append(f"身份证号 IN ({placeholders})")
            params.extend(value)

        # 处理姓名数组
        elif key == "姓名" and isinstance(value, list) and value:
            placeholders = ', '.join(['?'] * len(value))  # 动态生成占位符
            filters.append(f"姓名 IN ({placeholders})")
            params.extend(value)
        
        # 处理其他字段
        elif value not in [None, ""]:  # 跳过空字符串和 None
            filters.append(f"{key} = ?")
            params.append(value)
    
    # 生成 WHERE 条件
    where_clause = " AND ".join(filters) if filters else "1=1"
    
    # 需要统计的字段
    fields_to_group_by = {
        "BMI类型": "BMI类型",
        "吸烟量": "吸烟量",
        "是否吸烟": "是否吸烟",
        "性别": "性别",
        "是否居家": "是否居家",
        "是否锻炼": "是否锻炼",
        "是否饮酒": "是否饮酒",
        "饮酒频率": "饮酒频率",
        "健康分类": "健康分类"
    }

    connection = get_db_connection()
    cursor = connection.cursor()

    # 统计总条数
    total_query = f"SELECT COUNT(*) as total_num FROM users WHERE {where_clause}"
    cursor.execute(total_query, params)
    total_num = cursor.fetchone()['total_num']

    # 初始化统计结果
    stats = {}
    
    # 遍历需要统计的字段，分别执行 GROUP BY 查询
    for stat_name, field in fields_to_group_by.items():
        query = f"SELECT {field}, COUNT(*) as count FROM users WHERE {where_clause} GROUP BY {field}"
        cursor.execute(query, params)
        results = cursor.fetchall()
        stats[stat_name] = {row[field] if row[field] else "空值": row['count'] for row in results}

    # 如果总条数小于 100，查询并返回过滤后的数据
    data = []
    if total_num < 100:
        data_query = f"SELECT * FROM users WHERE {where_clause}"
        cursor.execute(data_query, params)
        data = [dict(row) for row in cursor.fetchall()]
        
        # 确保所有字段可序列化
        for row in data:
            for key, value in row.items():
                if isinstance(value, bytes):  # 将 bytes 类型转换为字符串
                    try:
                        row[key] = value.decode('utf-8')
                    except UnicodeDecodeError:
                        row[key] = "无法解码"  # 或者选择忽略
    
    connection.close()

    # 构建返回的 JSON 响应
    response_data = {
        "total_num": total_num,
    }

    # 动态添加统计结果
    response_data.update(stats)

    # 如果总条数小于 100，添加 data 字段
    if total_num < 100:
        response_data["data"] = data

    # 打印返回的数据以进行调试
    print(response_data, flush=True)

    return make_response(jsonify(response_data), 200)
