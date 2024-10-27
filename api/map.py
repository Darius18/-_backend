from math import radians, cos, sin, sqrt, atan2
from flask import jsonify, make_response, Blueprint, request
from datetime import datetime
from db import get_db_connection

map_bp = Blueprint('map', __name__)

# 计算两个坐标之间的距离（单位：公里）
def calculate_distance(lat1, lon1, lat2, lon2):
    if None in [lat1, lon1, lat2, lon2]:
        print("One of the coordinate values is None", flush=True)
    R = 6371  # 地球半径，单位为公里
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c  # 返回距离，单位为公里

# 修改聚合函数中的 '现住址' 部分为 'full_address' 字段，并截取前三个逗号前的内容
# 修改聚合函数中的 '现住址' 部分为 'full_address' 字段，并根据 level 提取逗号前的内容
def aggregate_points_by_level(points, radius_km, level):
    aggregated = []
    visited = [False] * len(points)

    for i, point in enumerate(points):
        if visited[i]:
            continue

        # 初始化当前聚合簇
        cluster = [point]
        visited[i] = True

        # 查找所有在当前点 radius_km 公里范围内的点，将它们聚合在一起
        for j in range(i + 1, len(points)):
            if visited[j]:
                continue
            distance = calculate_distance(point['lat'], point['lng'], points[j]['lat'], points[j]['lng'])

            # 如果距离在聚合半径内，将点加入聚合簇
            if distance <= radius_km:
                cluster.append(points[j])
                visited[j] = True
        def get_partial_address(full_address, level):
            parts = full_address.split(',')
            if level == 0 or level == 1:
                return ','.join(parts[:2])  # 提取前两个逗号前的内容
            elif level == 2:
                return ','.join(parts[:3])  # 提取前三个逗号前的内容
            elif level == 3:
                return ','.join(parts[:4]) if len(parts) > 3 else ','.join(parts[:3])  # 提取前4个逗号前的内容，若不足则取前三个
            else:
                return full_address  # 默认返回完整地址

        # 聚合簇的中心点
        center_lng = sum(p['lng'] for p in cluster) / len(cluster)
        center_lat = sum(p['lat'] for p in cluster) / len(cluster)

        aggregated_point = {
            'center': {
                'lng': center_lng,
                'lat': center_lat
            },
            'count': len(cluster),
            'addresses': [get_partial_address(cluster[0]['user_info']['full_address'], level)]
        }

        # 针对 level=3，添加详细数据，最多返回 10 条
        if level == 3:
            detailed_data = [
                {field: p['user_info'].get(field) for field in p['user_info']}
                for p in cluster[:10]  # 最多取前 10 条
            ]
            aggregated_point['detail_data'] = detailed_data

        aggregated.append(aggregated_point)

    return aggregated

@map_bp.route('/api/map', methods=['POST'])
def map_view():
    try:
        data = request.get_json()

        # 获取地理过滤请求参数
        level = data.get('level', 0)
        area = data.get('area', {})
        north_east = area.get('northEast', {})
        south_west = area.get('southWest', {})

        # 聚合半径配置，单位：公里
        level_config = {
            0: 3,   # 街道级别，半径3km
            1: 1,   # 社区级别，半径1km
            2: 0.3,  # 楼栋级别，半径300米
            3: 0.01   # 个人级别，半径10米
        }
        radius_km = level_config.get(level, 0.5)

        # 构建筛选条件
        filters = []
        params = []

        # 动态构建筛选条件
        for key, value in data.get('filter', {}).items():
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
            elif key == "身份证号" and isinstance(value, list) and value:
                placeholders = ', '.join(['?'] * len(value))
                filters.append(f"身份证号 IN ({placeholders})")
                params.extend(value)
            elif key == "姓名" and isinstance(value, list) and value:
                placeholders = ', '.join(['?'] * len(value))
                filters.append(f"姓名 IN ({placeholders})")
                params.extend(value)
            elif value not in [None, ""]:
                filters.append(f"{key} = ?")
                params.append(value)

        where_clause = " AND ".join(filters) if filters else "1=1"

        # 连接到数据库
        conn = get_db_connection()
        conn.enable_load_extension(True)
        conn.execute('SELECT load_extension("mod_spatialite")')
        cursor = conn.cursor()

        # 转换边界框的经纬度
        lng_min = south_west.get('lng')
        lat_min = south_west.get('lat')
        lng_max = north_east.get('lng')
        lat_max = north_east.get('lat')

        # 根据 level 选择查询的字段
        user_fields = [
            "姓名", "性别", "full_address", "出生日期", "健康分类", "慢病分类", "是否吸烟", 
            "开始吸烟时间", "戒断时间", "吸烟量", "是否饮酒", "饮酒类型", "饮酒量", 
            "饮酒频率", "戒酒日期", "是否锻炼", "锻炼情况", "每次锻炼时间", "锻炼类型", 
            "饮食习惯类型", "签约团队", "签约时间", "生效时间", "到期时间"
        ]

        # 使用空间索引进行地理范围查询，获取详细的用户数据
        query = f'''
            SELECT longitude, latitude, {', '.join(user_fields)}
            FROM users
            WHERE MbrWithin(geom, BuildMbr(?, ?, ?, ?))
            AND {where_clause}
        '''
        params = [lng_min, lat_min, lng_max, lat_max] + params

        cursor.execute(query, params)
        users = cursor.fetchall()

        window_points = []
        for user in users:
            lng = user['longitude']
            lat = user['latitude']

            user_info = dict(user)
            window_points.append({
                'lng': lng,
                'lat': lat,
                'user_info': user_info
            })

        # 聚合点，基于不同的level半径
        aggregated_points = aggregate_points_by_level(window_points, radius_km, level)

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
                    "现住址": list(set(point['addresses']))
                }
            }

            # 如果是 level == 3，添加详细用户信息
            if level == 3 and 'detail_data' in point:
                feature['properties']['detail_data'] = point['detail_data']

            feature_collection["features"].append(feature)

        return make_response(jsonify(feature_collection), 200)

    except Exception as e:
        return make_response(jsonify({'error': str(e)}), 500)