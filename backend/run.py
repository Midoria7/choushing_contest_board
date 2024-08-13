from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import json

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Optionally, you can specify origins
# CORS(app, origins=["http://localhost:5173"])

# 加载配置文件
with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

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
    username = data.get('username')
    problem_name = data.get('problem_name')
    score = data.get('score')

    if problem_name not in config['problems']:
        return jsonify({'error': '题名不合法'}), 400

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
