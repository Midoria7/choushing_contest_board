import json
import sqlite3
import time
from flask_cors import CORS
import requests
from flask import Flask, request, jsonify

# 加载配置文件
with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

# 从配置文件中读取配置参数
COMPETITION_NAME = config['competition_name']
DESCRIPTION = config['description']
PROBLEMS = config['problems']
START_TIME = config['start_time']
END_TIME = config['end_time']
ADMIN_TOKEN = config['admin_token']
FEISHU_APP_ID = config['feishu_app_id']
FEISHU_APP_SECRET = config['feishu_app_secret']
FEISHU_APP_TOKEN = config['feishu_app_token']
FEISHU_TABLE_ID = config['feishu_table_id']

# 全局变量来存储 Feishu token 和过期时间
feishu_tenant_access_token = None
feishu_token_expiration = 0

def get_feishu_token():
    global feishu_tenant_access_token, feishu_token_expiration

    # 检查 token 是否已经存在且未过期
    if feishu_tenant_access_token and time.time() < feishu_token_expiration:
        return feishu_tenant_access_token

    # 获取新的 token
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    headers = {
        "Content-Type": "application/json"
    }
    body = {
        "app_id": FEISHU_APP_ID,
        "app_secret": FEISHU_APP_SECRET
    }

    response = requests.post(url, json=body)
    data = response.json()

    if data["code"] != 0:
        raise Exception(f"Failed to get Feishu token: {data['msg']}")

    feishu_tenant_access_token = data["tenant_access_token"]

    # 记录过期时间，假设 token 有效期为 2 小时
    feishu_token_expiration = time.time() + 2 * 60 * 60 - 15

    return feishu_tenant_access_token

def get_username_by_token(token):
    feishu_token = get_feishu_token()
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{FEISHU_APP_TOKEN}/tables/{FEISHU_TABLE_ID}/records/search"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {feishu_token}"
    }

    body = {
        "field_names": ["兑换码", "分配用户"],
        "filter": {
            "conjunction": "and",
            "conditions": [
                {
                    "field_name": "兑换码",
                    "operator": "is",
                    "value": [token]
                }
            ]
        },
        "automatic_fields": True
    }

    response = requests.post(url, json=body, headers=headers)
    data = response.json()

    if data["code"] != 0 or len(data["data"]["items"]) == 0:
        raise Exception(f"Failed to get user by token: {data['msg']}")

    record = data["data"]["items"][0]
    username = record["fields"]["分配用户"][0]["text"]

    return username

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Optionally, you can specify origins
# CORS(app, origins=["http://localhost:5173"])

# 初始化数据库
def init_db():
    conn = sqlite3.connect('competition.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            problem_name TEXT NOT NULL,
            score INTEGER NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# 插入或更新提交记录
def upsert_submission(username, problem_name, score):
    conn = sqlite3.connect('competition.db')
    c = conn.cursor()

    # 检查是否有更高的分数
    c.execute('''
        SELECT score FROM submissions
        WHERE username = ? AND problem_name = ?
    ''', (username, problem_name))
    row = c.fetchone()

    if row is None:
        # 新增记录
        c.execute('''
            INSERT INTO submissions (username, problem_name, score)
            VALUES (?, ?, ?)
        ''', (username, problem_name, score))
    else:
        # 仅更新更高的分数
        existing_score = row[0]
        if score > existing_score:
            c.execute('''
                UPDATE submissions
                SET score = ?
                WHERE username = ? AND problem_name = ?
            ''', (score, username, problem_name))

    conn.commit()
    conn.close()

# POST 请求：新增提交
@app.route('/submit', methods=['POST'])
def submit_score():
    data = request.get_json()
    problem_name = data.get('problem_name')
    score = data.get('score')
    token = data.get('token')
    username = data.get('username')

    if not problem_name or not score or not token:
        return jsonify({'error': 'Missing required parameters'}), 400

    # 检查题名是否合法
    if problem_name not in PROBLEMS:
        return jsonify({'error': 'Invalid problem name'}), 400

    # 检查是否是管理员
    if token == ADMIN_TOKEN:
        if not username:
            return jsonify({'error': 'Username is required for admin submissions'}), 400
    else:
        # 普通用户，通过兑换码查询用户名
        try:
            assigned_username = get_username_by_token(token)
        except Exception as e:
            return jsonify({'error': str(e)}), 400

        # 如果用户名存在，检查是否与查询到的用户名匹配
        if username and username != assigned_username:
            return jsonify({'error': 'Username does not match the assigned user'}), 400

        # 使用查询到的用户名
        username = assigned_username

    upsert_submission(username, problem_name, score)
    return jsonify({'message': '提交成功'}), 200

# GET 请求：获取比赛信息
@app.route('/competition_info', methods=['GET'])
def get_competition_info():
    return jsonify({
        'competition_name': config['competition_name'],
        'description': config['description'],
        'problems': config['problems'],
        'start_time': config['start_time'],
        'end_time': config['end_time']
    })

# GET 请求：获取排榜信息
@app.route('/leaderboard', methods=['GET'])
def get_leaderboard():
    problem_leaderboards = {}
    conn = sqlite3.connect('competition.db')
    c = conn.cursor()

    for problem in config['problems']:
        c.execute('''
            SELECT username, MAX(score) as max_score
            FROM submissions
            WHERE problem_name = ?
            GROUP BY username
            ORDER BY max_score DESC
        ''', (problem,))
        problem_leaderboards[problem] = [{'username': row[0], 'score': row[1]} for row in c.fetchall()]

    conn.close()
    return jsonify(problem_leaderboards)

if __name__ == '__main__':
    init_db()
    # app.run(debug=True)
    app.run(host='0.0.0.0', port=5000, debug=True)
