from flask import Flask, request, jsonify
from datetime import datetime
import sqlite3
import os

app = Flask(__name__)

# Настройка базы данных
DATABASE = 'attention_checks.db'

def init_db():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                machine_id TEXT NOT NULL,
                registered_at TEXT NOT NULL,
                UNIQUE(username, machine_id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                machine_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                attempts INTEGER,
                response_time REAL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')
        conn.commit()

@app.route('/api/register', methods=['POST'])
def register_user():
    data = request.json
    username = data.get('username')
    machine_id = data.get('machine_id')
    
    if not username or not machine_id:
        return jsonify({'error': 'Необходимо указать username и machine_id'}), 400
    
    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO users (username, machine_id, registered_at) VALUES (?, ?, ?)',
                (username, machine_id, datetime.now().isoformat())
            )
            user_id = cursor.lastrowid
            conn.commit()
        
        return jsonify({
            'status': 'success',
            'user_id': user_id
        }), 200
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Пользователь с таким именем уже зарегистрирован на этой машине'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/logs', methods=['POST'])
def add_log():
    data = request.json
    user_id = data.get('user_id')
    machine_id = data.get('machine_id')
    
    if not user_id or not machine_id:
        return jsonify({'error': 'Необходимо указать user_id и machine_id'}), 400
    
    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute(
                '''INSERT INTO logs 
                (user_id, machine_id, event_type, attempts, response_time, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)''',
                (
                    user_id,
                    machine_id,
                    data.get('event_type'),
                    data.get('attempts'),
                    data.get('response_time'),
                    data.get('timestamp', datetime.now().isoformat())
                )
            )
            conn.commit()
        
        return jsonify({'status': 'success'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/users', methods=['GET'])
def get_users():
    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, username, machine_id, registered_at FROM users')
            users = cursor.fetchall()
        
        return jsonify([{
            'id': user[0],
            'username': user[1],
            'machine_id': user[2],
            'registered_at': user[3]
        } for user in users]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/logs/<int:user_id>', methods=['GET'])
def get_user_logs(user_id):
    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT event_type, attempts, response_time, timestamp 
                FROM logs 
                WHERE user_id = ?
                ORDER BY timestamp DESC
            ''', (user_id,))
            logs = cursor.fetchall()
        
        return jsonify([{
            'event_type': log[0],
            'attempts': log[1],
            'response_time': log[2],
            'timestamp': log[3]
        } for log in logs]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)
