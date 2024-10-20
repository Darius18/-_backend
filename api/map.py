from flask import jsonify, make_response, Blueprint, request
import sqlite3
from math import radians, cos, sin, sqrt, atan2

# 定义一个 Blueprint
map_bp = Blueprint('map', __name__)

# 数据库连接函数
def get_db_connection():
    """Connects to the SQLite database."""
    connection = sqlite3.connect('medical_users.db')
    connection.row_factory = sqlite3.Row  # 使我们可以以字典形式访问列
    return connection

# 计算两个坐标之间的距离（Haversine公式）
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371  # 地球半径，单位为公里
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c  # 返回距离，单位为公里

# 判断点是否在给定区域内
def is_point_in_area(lng, lat, north_east, south_west):
    return (south_west['lng'] <= lng <= north_east['lng']) and (south_west['lat'] <= lat <= north_east['lat'])

# 聚合函数
def aggregate_points(points, radius):
    aggregated = []
    visited = [False] * len(points)

    for i, point in enumerate(points):
        if visited[i]:
            continue
        cluster = [point]
        visited[i] = True

        for j in range(i + 1, len(points)):
            if visited[j]:
                continue
            distance = calculate_distance(point['lat'], point['lng'], points[j]['lat'], points[j]['lng'])
            if distance <= radius:
                cluster.append(points[j])
                visited[j] = True
        
        # 聚合中心点及包含的用户住址信息
        aggregated.append({
            'center': {
                'lng': sum(p['lng'] for p in cluster) / len(cluster),
                'lat': sum(p['lat'] for p in cluster) / len(cluster)
            },
            'count': len(cluster),
            'addresses': [p['user_info']['现住址'] for p in cluster]  # 将现住址收集为列表
        })
    
    return aggregated

# 处理/api/map的POST请求
@map_bp.route('/api/map', methods=['POST'])
def map_view():
    try:
        data = request.get_json()

        # 获取请求参数
        level = data.get('level', 0)
        area = data.get('area', {})

        north_east = area.get('northEast', {})
        south_west = area.get('southWest', {})

        # 聚合半径配置
        level_config = {
            0: 0.005,  # 街道级别
            1: 0.002,  # 社区级别
            2: 0.0003,  # 楼栋级别
            3: 0.00005  # 个人级别
        }
        radius = level_config.get(level, 0.005)  # 默认街道级别

        # 查询数据库
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users')
        users = cursor.fetchall()

        window_points = []
        
        for user in users:
            location = user['location']
            lng, lat = map(float, location.split(','))  # 将location字段中的字符串分割为经纬度

            # 判断是否在请求的区域内
            if is_point_in_area(lng, lat, north_east, south_west):
                window_points.append({
                    'lng': lng,
                    'lat': lat,
                    'user_info': dict(user)  # 将数据库中的该用户信息添加到返回结果中
                })

        # 聚合点
        aggregated_points = aggregate_points(window_points, radius)

        # 构造返回结果的 GeoJSON 格式
        feature_collection = {
            "type": "FeatureCollection",
            "features": []
        }

        for point in aggregated_points:
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [point['center']['lng'], point['center']['lat']]
                },
                "properties": {
                    "count": point['count'],
                    "现住址": list(set(point['addresses']))  # 使用 set 去重后转回列表
                }
            }
            feature_collection["features"].append(feature)

        return make_response(jsonify(feature_collection), 200)
    except Exception as e:
        return make_response(jsonify({'error': str(e)}), 500)
