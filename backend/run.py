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
IS_AUTH_ENABLED = config['is_auth_enabled']
ADMIN_TOKEN = config['admin_token']
FEISHU_APP_ID = config['feishu_app_id']
FEISHU_APP_SECRET = config['feishu_app_secret']
FEISHU_APP_TOKEN = config['feishu_app_token']
FEISHU_TABLE_ID = config['feishu_table_id']
FEISHU_QUERY_TOKEN_NAME = config['feishu_query_token_name']
FEISHU_QUERY_ONLYID_NAME = config['feishu_query_onlyid_name']
FEISHU_QUERY_USERNAME_NAME = config['feishu_query_username_name']

# 全局变量来存储 Feishu token 和过期时间
feishu_tenant_access_token = None
feishu_token_expiration = 0

def get_feishu_token():
    global feishu_tenant_access_token, feishu_token_expiration

    if feishu_tenant_access_token and time.time() < feishu_token_expiration:
        return feishu_tenant_access_token

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
    feishu_token_expiration = time.time() + 2 * 60 * 60 - 15

    return feishu_tenant_access_token

def get_user_info_by_token(token):
    feishu_token = get_feishu_token()
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{FEISHU_APP_TOKEN}/tables/{FEISHU_TABLE_ID}/records/search"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {feishu_token}"
    }

    body = {
        "field_names": [FEISHU_QUERY_TOKEN_NAME, FEISHU_QUERY_ONLYID_NAME, FEISHU_QUERY_USERNAME_NAME],
        "filter": {
            "conjunction": "and",
            "conditions": [
                {
                    "field_name": FEISHU_QUERY_TOKEN_NAME,
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
        raise Exception(f"Failed to get user info by token: {data['msg']}")

    record = data["data"]["items"][0]
    onlyid = record["fields"][FEISHU_QUERY_ONLYID_NAME][0]["text"]
    username = record["fields"][FEISHU_QUERY_USERNAME_NAME][0]["text"]

    return onlyid, username

app = Flask(__name__)
CORS(app)

def init_db():
    conn = sqlite3.connect('competition.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            onlyid TEXT NOT NULL,
            username TEXT NOT NULL,
            problem_name TEXT NOT NULL,
            score INTEGER NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def upsert_submission(onlyid, username, problem_name, score):
    conn = sqlite3.connect('competition.db')
    c = conn.cursor()

    c.execute('''
        SELECT score FROM submissions
        WHERE onlyid = ? AND problem_name = ?
    ''', (onlyid, problem_name))
    row = c.fetchone()

    if row is None:
        c.execute('''
            INSERT INTO submissions (onlyid, username, problem_name, score)
            VALUES (?, ?, ?, ?)
        ''', (onlyid, username, problem_name, score))
    else:
        existing_score = row[0]
        if score > existing_score:
            c.execute('''
                UPDATE submissions
                SET score = ?, username = ?
                WHERE onlyid = ? AND problem_name = ?
            ''', (score, username, onlyid, problem_name))

    conn.commit()
    conn.close()

@app.route('/submit', methods=['POST'])
def submit_score():
    data = request.get_json()
    problem_name = data.get('problem_name')
    score = data.get('score')
    token = data.get('token')
    onlyid = data.get('onlyid')
    username = data.get('username')

    if not problem_name or not score:
        return jsonify({'error': 'Missing required parameters'}), 400

    if problem_name not in PROBLEMS:
        return jsonify({'error': 'Invalid problem name'}), 400

    if IS_AUTH_ENABLED:
        if token == ADMIN_TOKEN:
            if not onlyid or not username:
                return jsonify({'error': 'Onlyid and username are required for admin submissions'}), 400
        else:
            try:
                assigned_onlyid, assigned_username = get_user_info_by_token(token)
            except Exception as e:
                return jsonify({'error': str(e)}), 400

            if onlyid and onlyid != assigned_onlyid:
                return jsonify({'error': 'Onlyid does not match the assigned user'}), 400
            if username and username != assigned_username:
                return jsonify({'error': 'Username does not match the assigned user'}), 400

            onlyid = assigned_onlyid
            username = assigned_username
    else:
        if not onlyid or not username:
            return jsonify({'error': 'Onlyid and username are required'}), 400

    upsert_submission(onlyid, username, problem_name, score)
    return jsonify({'message': '提交成功'}), 200

@app.route('/competition_info', methods=['GET'])
def get_competition_info():
    return jsonify({
        'competition_name': config['competition_name'],
        'description': config['description'],
        'problems': config['problems'],
        'start_time': config['start_time'],
        'end_time': config['end_time']
    })

@app.route('/leaderboard', methods=['GET'])
def get_leaderboard():
    problem_leaderboards = {}
    conn = sqlite3.connect('competition.db')
    c = conn.cursor()

    for problem in config['problems']:
        c.execute('''
            SELECT onlyid, username, MAX(score) as max_score
            FROM submissions
            WHERE problem_name = ?
            GROUP BY onlyid, username
            ORDER BY max_score DESC
        ''', (problem,))
        problem_leaderboards[problem] = [
            {'onlyid': row[0], 'username': row[1], 'score': row[2]} 
            for row in c.fetchall()
        ]

    conn.close()
    return jsonify(problem_leaderboards)

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=config['port'], debug=config['debug'])
