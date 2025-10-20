from flask import Flask, request, jsonify
from functools import wraps
import sqlite3
import hashlib
import time
import os
from datetime import datetime, timedelta

app = Flask(__name__)

API_KEY = os.getenv('API_KEY', 'YOUR_SECRET_API_KEY')
DATABASE = 'anticheat.db'

def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS verified_users
                 (user_id TEXT PRIMARY KEY,
                  oculus_id TEXT,
                  first_verified TIMESTAMP,
                  last_verified TIMESTAMP,
                  verification_count INTEGER)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS banned_users
                 (user_id TEXT PRIMARY KEY,
                  reason TEXT,
                  banned_at TIMESTAMP,
                  expires_at TIMESTAMP,
                  evidence TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS security_reports
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id TEXT,
                  reason TEXT,
                  evidence TEXT,
                  reported_at TIMESTAMP)''')
    
    conn.commit()
    conn.close()

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key or api_key != API_KEY:
            return jsonify({'error': 'Invalid API key'}), 401
        return f(*args, **kwargs)
    return decorated_function

@app.route('/api/verify', methods=['POST'])
@require_api_key
def verify_user():
    try:
        user_id = request.form.get('userID')
        app_id = request.form.get('appID')
        platform = request.form.get('platform')
        
        if not user_id or not app_id:
            return jsonify({'verified': False, 'error': 'Missing parameters'}), 400
        
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        
        c.execute('SELECT * FROM banned_users WHERE user_id = ? AND (expires_at IS NULL OR expires_at > ?)',
                  (user_id, datetime.now()))
        ban = c.fetchone()
        
        if ban:
            conn.close()
            return jsonify({
                'verified': False,
                'banned': True,
                'reason': ban[1],
                'expires_at': ban[3]
            }), 403
        
        c.execute('SELECT * FROM verified_users WHERE user_id = ?', (user_id,))
        existing = c.fetchone()
        
        if existing:
            c.execute('''UPDATE verified_users 
                        SET last_verified = ?, verification_count = verification_count + 1 
                        WHERE user_id = ?''',
                     (datetime.now(), user_id))
        else:
            c.execute('''INSERT INTO verified_users 
                        (user_id, oculus_id, first_verified, last_verified, verification_count) 
                        VALUES (?, ?, ?, ?, 1)''',
                     (user_id, app_id, datetime.now(), datetime.now()))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'verified': True,
            'user_id': user_id,
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({'verified': False, 'error': str(e)}), 500

@app.route('/api/ban', methods=['POST'])
@require_api_key
def ban_user():
    try:
        user_id = request.form.get('userID')
        reason = request.form.get('reason')
        evidence = request.form.get('evidence', '')
        duration_hours = int(request.form.get('durationHours', 0))
        
        if not user_id or not reason:
            return jsonify({'success': False, 'error': 'Missing parameters'}), 400
        
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        
        expires_at = None if duration_hours == 0 else datetime.now() + timedelta(hours=duration_hours)
        
        c.execute('''INSERT OR REPLACE INTO banned_users 
                    (user_id, reason, banned_at, expires_at, evidence) 
                    VALUES (?, ?, ?, ?, ?)''',
                 (user_id, reason, datetime.now(), expires_at, evidence))
        
        c.execute('''INSERT INTO security_reports 
                    (user_id, reason, evidence, reported_at) 
                    VALUES (?, ?, ?, ?)''',
                 (user_id, reason, evidence, datetime.now()))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'banned_until': expires_at.isoformat() if expires_at else 'permanent'
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/check_ban/<user_id>', methods=['GET'])
@require_api_key
def check_ban(user_id):
    try:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        
        c.execute('SELECT * FROM banned_users WHERE user_id = ? AND (expires_at IS NULL OR expires_at > ?)',
                  (user_id, datetime.now()))
        ban = c.fetchone()
        
        conn.close()
        
        if ban:
            return jsonify({
                'banned': True,
                'reason': ban[1],
                'banned_at': ban[2],
                'expires_at': ban[3]
            }), 200
        else:
            return jsonify({'banned': False}), 200
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/reports', methods=['GET'])
@require_api_key
def get_reports():
    try:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        
        c.execute('SELECT * FROM security_reports ORDER BY reported_at DESC LIMIT 100')
        reports = c.fetchall()
        
        conn.close()
        
        return jsonify({
            'reports': [
                {
                    'id': r[0],
                    'user_id': r[1],
                    'reason': r[2],
                    'evidence': r[3],
                    'reported_at': r[4]
                }
                for r in reports
            ]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=False)
