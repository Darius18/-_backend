from flask import jsonify, make_response, Blueprint
import sqlite3


# 定义一个 Blueprint
chart_bp = Blueprint('chart', __name__)

def get_db_connection():
    """Connects to the SQLite database."""
    connection = sqlite3.connect('medical_users.db')
    connection.row_factory = sqlite3.Row  # This allows us to access columns by name
    return connection

def get_age_distribution():
    """Fetches age distribution from the users table in the database."""
    age_distribution = {f'{i}-{i + 9}': 0 for i in range(0, 100, 10)}

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT 年龄 FROM users')

        rows = cursor.fetchall()
        for row in rows:
            age = row['年龄']
            if age != "":
                age = int(age)
            else:
                continue

            for i in range(0, 100, 10):
                if i <= age < i + 10:
                    age_distribution[f'{i}-{i + 9}'] += 1
                    break
        conn.close()
    except Exception as e:
        return {'error': str(e)}, 500
    return age_distribution

def get_health_distribution():
    """Fetches health distribution from the users table in the database."""
    health_distribution = {}

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT 健康分类 FROM users')

        rows = cursor.fetchall()
        for row in rows:
            health_category = row['健康分类']
            if health_category in health_distribution:
                health_distribution[health_category] += 1
            else:
                health_distribution[health_category] = 1

        conn.close()
    except Exception as e:
        return {'error': str(e)}, 500
    return health_distribution

def get_bmi_distribution():
    """Fetches BMI distribution from the users table in the database."""
    bmi_distribution = {
        '正常': 0,
        '超重': 0,
        '肥胖': 0,
        '消瘦': 0
    }

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT BMI FROM users')

        rows = cursor.fetchall()
        for row in rows:
            bmi = row['BMI']
            if bmi != "":
                bmi = float(bmi)
            else:
                continue

            if 18.5 <= bmi < 24.0:
                bmi_distribution['正常'] += 1
            elif 24.0 <= bmi < 28.0:
                bmi_distribution['超重'] += 1
            elif bmi >= 28.0:
                bmi_distribution['肥胖'] += 1
            elif bmi < 18.5:
                bmi_distribution['消瘦'] += 1

        conn.close()
    except Exception as e:
        return {'error': str(e)}, 500
    return bmi_distribution

def get_smoking_distribution():
    """Fetches smoking amount distribution from the users table in the database."""
    smoking_distribution = {}

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT 吸烟量 FROM users')

        rows = cursor.fetchall()
        for row in rows:
            smoking_amount = row['吸烟量']
            if smoking_amount != "":
                if smoking_amount in smoking_distribution:
                    smoking_distribution[smoking_amount] += 1
                else:
                    smoking_distribution[smoking_amount] = 1

        conn.close()
    except Exception as e:
        return {'error': str(e)}, 500
    return smoking_distribution

def get_right_bottom_distribution():
    """Fetches right bottom distribution (居家/建档/签约) from the users table."""
    right_bottom_distribution = {
        '居家': 0,
        '不居家': 0,
        '已建档': 0,
        '未建档': 0,
        '已签约': 0,
        '未签约': 0
    }

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT 是否居家, 是否建档, 是否签约 FROM users')

        rows = cursor.fetchall()
        for row in rows:
            if row['是否居家'] == '是':
                right_bottom_distribution['居家'] += 1
            elif row['是否居家'] == '否':
                right_bottom_distribution['不居家'] += 1

            if row['是否建档'] == '是':
                right_bottom_distribution['已建档'] += 1
            elif row['是否建档'] == '否':
                right_bottom_distribution['未建档'] += 1

            if row['是否签约'] == '是':
                right_bottom_distribution['已签约'] += 1
            elif row['是否签约'] == '否':
                right_bottom_distribution['未签约'] += 1

        conn.close()
    except Exception as e:
        return {'error': str(e)}, 500
    return right_bottom_distribution

def get_total_num():
    """Fetches the total number of users from the users table."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) AS total FROM users')
        total_num = cursor.fetchone()['total']
        conn.close()
    except Exception as e:
        return {'error': str(e)}, 500
    return total_num

def get_left_bottom_distribution():
    """Fetches left bottom distribution (高血压患病率, 糖尿病患病率, 血糖控制率, 血压控制率) from the users table."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        total_num = get_total_num()
        if isinstance(total_num, dict):  # check if total_num returned an error
            return total_num

        left_bottom_distribution = {
            '高血压患病率': 0.0,
            '糖尿病患病率': 0.0,
            '血糖控制率': 0.0,
            '血压控制率': 0.0
        }

        cursor.execute('SELECT COUNT(*) AS hypertension_count FROM users WHERE 是否有高血压="是"')
        hypertension_count = cursor.fetchone()['hypertension_count']
        left_bottom_distribution['高血压患病率'] = round(hypertension_count / total_num, 4)

        cursor.execute('SELECT COUNT(*) AS diabetes_count FROM users WHERE 是否有糖尿病="是"')
        diabetes_count = cursor.fetchone()['diabetes_count']
        left_bottom_distribution['糖尿病患病率'] = round(diabetes_count / total_num, 4)

        cursor.execute('SELECT 空腹血糖 FROM users')
        rows = cursor.fetchall()
        blood_sugar_control_count = 0
        for row in rows:
            fasting_blood_sugar = row['空腹血糖']
            if fasting_blood_sugar not in ["无", "", None]:
                if float(fasting_blood_sugar) < 7.0:
                    blood_sugar_control_count += 1
        left_bottom_distribution['血糖控制率'] = round(blood_sugar_control_count / total_num, 4)

        cursor.execute('SELECT 年龄, 收缩压, 舒张压 FROM users')
        rows = cursor.fetchall()
        controlled_blood_pressure_count = 0
        for row in rows:
            age = row['年龄']
            systolic_pressure = row['收缩压']
            diastolic_pressure = row['舒张压']

            if age not in ["无", "", None] and systolic_pressure not in ["无", "", None] and diastolic_pressure not in ["无", "", None]:
                age = int(age)
                systolic_pressure = int(systolic_pressure)
                diastolic_pressure = int(diastolic_pressure)

                if age < 65:
                    if systolic_pressure < 140 and diastolic_pressure < 90:
                        controlled_blood_pressure_count += 1
                else:
                    if systolic_pressure < 150 and diastolic_pressure < 90:
                        controlled_blood_pressure_count += 1

        left_bottom_distribution['血压控制率'] = round(controlled_blood_pressure_count / total_num, 4)

        conn.close()
    except Exception as e:
        return {'error': str(e)}, 500
    return left_bottom_distribution

def calculate_percent_distribution(distribution, total_num):
    """Calculates percentage distribution and retains up to 6 decimal points."""
    percent_distribution = {key: round(value / total_num, 6) for key, value in distribution.items()}
    return percent_distribution

@chart_bp.route('/api/charts', methods=['GET'])
def charts():
    """API endpoint to return age, health, BMI, smoking, right bottom distribution, left bottom distribution, and total number of users as JSON."""
    try:
        age_distribution = get_age_distribution()
        health_distribution = get_health_distribution()
        bmi_distribution = get_bmi_distribution()
        smoking_distribution = get_smoking_distribution()
        right_bottom_distribution = get_right_bottom_distribution()
        left_bottom_distribution = get_left_bottom_distribution()
        total_num = get_total_num()

        # Check for any errors in the individual functions
        if isinstance(age_distribution, dict) and 'error' in age_distribution:
            return make_response(jsonify(age_distribution), 500)
        if isinstance(health_distribution, dict) and 'error' in health_distribution:
            return make_response(jsonify(health_distribution), 500)
        if isinstance(bmi_distribution, dict) and 'error' in bmi_distribution:
            return make_response(jsonify(bmi_distribution), 500)
        if isinstance(smoking_distribution, dict) and 'error' in smoking_distribution:
            return make_response(jsonify(smoking_distribution), 500)
        if isinstance(right_bottom_distribution, dict) and 'error' in right_bottom_distribution:
            return make_response(jsonify(right_bottom_distribution), 500)
        if isinstance(left_bottom_distribution, dict) and 'error' in left_bottom_distribution:
            return make_response(jsonify(left_bottom_distribution), 500)
        if isinstance(total_num, dict) and 'error' in total_num:
            return make_response(jsonify(total_num), 500)

        # 计算 health_distribution_percent 和 smoking_distribution_percent
        health_distribution_percent = calculate_percent_distribution(health_distribution, total_num)
        smoking_distribution_percent = calculate_percent_distribution(smoking_distribution, total_num)

        return jsonify({
            'age_distribution': age_distribution,
            'health_distribution': health_distribution,
            'health_distribution_percent': health_distribution_percent,
            'bmi_distribution': bmi_distribution,
            'smoking_distribution': smoking_distribution,
            'smoking_distribution_percent': smoking_distribution_percent,
            'right_bottom': right_bottom_distribution,
            'left_bottom': left_bottom_distribution,
            'total_num': total_num
        })
    except Exception as e:
        return make_response(jsonify({'error': str(e)}), 500)