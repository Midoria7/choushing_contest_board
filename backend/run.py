import json
import sqlite3
import time
from flask_cors import CORS
import requests
from flask import Flask, request, jsonify
from datetime import datetime, timezone, timedelta

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

    if data["code"] != 0:
        raise Exception(f"Failed to get user info by token: {data['msg']}")
    
    if len(data["data"]["items"]) == 0:
        raise Exception("Cannot find user info by token")

    record = data["data"]["items"][0]
    onlyid = record["fields"][FEISHU_QUERY_ONLYID_NAME][0]["text"]
    username = record["fields"][FEISHU_QUERY_USERNAME_NAME][0]["text"]

    return onlyid, username

def get_username_by_onlyid(onlyid):
    feishu_token = get_feishu_token()
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{FEISHU_APP_TOKEN}/tables/{FEISHU_TABLE_ID}/records/search"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {feishu_token}"
    }

    body = {
        "field_names": [FEISHU_QUERY_ONLYID_NAME, FEISHU_QUERY_USERNAME_NAME],
        "filter": {
            "conjunction": "and",
            "conditions": [
                {
                    "field_name": FEISHU_QUERY_ONLYID_NAME,
                    "operator": "is",
                    "value": [onlyid]
                }
            ]
        },
        "automatic_fields": True
    }

    response = requests.post(url, json=body, headers=headers)
    data = response.json()

    if data["code"] != 0 or len(data["data"]["items"]) == 0:
        raise Exception(f"Failed to get username by onlyid: {data['msg']}")

    record = data["data"]["items"][0]
    username = record["fields"][FEISHU_QUERY_USERNAME_NAME][0]["text"]

    return username

def calculate_submission_time():
    start_time = datetime.fromisoformat(START_TIME).astimezone(timezone(timedelta(hours=8)))
    now = datetime.now(timezone(timedelta(hours=8)))  # 使用 UTC+8 时区
    return int((now - start_time).total_seconds())

app = Flask(__name__)
CORS(app)

def init_db():
    conn = sqlite3.connect('competition.db')
    c = conn.cursor()
    
    # 初始化 submissions 表
    c.execute('''
        CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            onlyid TEXT NOT NULL,
            username TEXT NOT NULL,
            problem_name TEXT NOT NULL,
            score INTEGER NOT NULL,
            submission_time INTEGER NOT NULL,
            log TEXT NOT NULL
        )
    ''')

    # 初始化 submissionrecords 表
    c.execute('''
        CREATE TABLE IF NOT EXISTS submissionrecords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            onlyid TEXT NOT NULL,
            username TEXT NOT NULL,
            problem_name TEXT NOT NULL,
            score INTEGER NOT NULL,
            submission_time INTEGER NOT NULL,
            log TEXT NOT NULL
        )
    ''')
    
    conn.commit()
    conn.close()

def upsert_submission(onlyid, username, problem_name, score, submission_time, log):
    conn = sqlite3.connect('competition.db')
    c = conn.cursor()

    # 更新 submissions 表
    c.execute('''
        SELECT score, submission_time FROM submissions
        WHERE onlyid = ? AND problem_name = ?
    ''', (onlyid, problem_name))
    row = c.fetchone()

    if row is None:
        c.execute('''
            INSERT INTO submissions (onlyid, username, problem_name, score, submission_time, log)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (onlyid, username, problem_name, score, submission_time, log))
    else:
        existing_score = row[0]
        existing_time = row[1]
        if score > existing_score:
            c.execute('''
                UPDATE submissions
                SET score = ?, submission_time = ?, username = ?, log = ?
                WHERE onlyid = ? AND problem_name = ?
            ''', (score, submission_time, username, log, onlyid, problem_name))

    # 插入记录到 submissionrecords 表
    c.execute('''
        INSERT INTO submissionrecords (onlyid, username, problem_name, score, submission_time, log)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (onlyid, username, problem_name, score, submission_time, log))

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
    log = data.get('log')

    if not problem_name or score is None or not log:
        return jsonify({'error': 'Missing required parameters'}), 400

    if score < 0:
        return jsonify({'error': 'Score must be a non-negative integer'}), 400
    
    if score == 0:
        return jsonify({'message': 'score is 0, not submit'}), 200

    if problem_name not in PROBLEMS:
        return jsonify({'error': 'Invalid problem name'}), 400
    
    # 检查提交时间是否在比赛时间内
    start_time = datetime.fromisoformat(START_TIME).astimezone(timezone(timedelta(hours=8)))
    end_time = datetime.fromisoformat(END_TIME).astimezone(timezone(timedelta(hours=8)))
    current_time = datetime.now(timezone(timedelta(hours=8)))

    if not (start_time <= current_time <= end_time):
        return jsonify({'error': 'Submission time is outside of the competition period'}), 400

    submission_time = calculate_submission_time()

    if IS_AUTH_ENABLED:
        if token == ADMIN_TOKEN:
            if not onlyid:
                return jsonify({'error': 'Onlyid is required for admin submissions'}), 400
            
            try:
                assigned_username = get_username_by_onlyid(onlyid)
                if username and username != assigned_username:
                    return jsonify({'error': 'Username does not match the assigned user'}), 400
                username = assigned_username
            except Exception as e:
                return jsonify({'error': str(e)}), 400

        else:
            # 普通用户，通过兑换码查询用户名和学号
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

    upsert_submission(onlyid, username, problem_name, score, submission_time, log)
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
            SELECT onlyid, username, MAX(score) as max_score, MIN(submission_time) as min_submission_time
            FROM submissions
            WHERE problem_name = ?
            GROUP BY onlyid, username
            ORDER BY max_score DESC, min_submission_time ASC
        ''', (problem,))
        problem_leaderboards[problem] = [
            {'onlyid': row[0], 'username': row[1], 'score': row[2], 'submission_time': row[3]} 
            for row in c.fetchall()
        ]

    conn.close()
    return jsonify(problem_leaderboards)

init_db()
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=config['port'], debug=config['debug'])
