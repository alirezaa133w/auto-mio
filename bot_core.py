"""
ربات اصلی - با Session قبلی
"""

import json
import random
import time
import threading
import os
from telethon.sync import TelegramClient

# ========== تنظیمات ==========
API_ID = 17187664
API_HASH = 'd6eae2c921342bb71816a980dc11b9f5'
USERS_FILE = 'users.json'
SESSIONS_DIR = 'sessions/'
ACTIVE_SESSIONS = {}

KEYWORDS = ["میو", "مع", "میاو", "معو"]
DELAYS = list(range(260, 361, 5))

# ========== مدیریت فایل‌ها ==========
def load_users():
    try:
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def update_user_status(user_id, status, data=None):
    users = load_users()
    user_id = str(user_id)
    if user_id not in users:
        users[user_id] = {}
    users[user_id]['status'] = status
    if data:
        users[user_id].update(data)
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)

# ========== کلاس ربات کاربر ==========
class UserBot:
    def __init__(self, user_id, data):
        self.user_id = user_id
        self.phone = data.get('phone')
        self.group_link = data.get('group_link', 'https://t.me/+NJNJp5hUf3IzNTRk')
        self.client = None
        self.running = False
        
    def start(self):
        session_file = f"{SESSIONS_DIR}user_{self.user_id}.session"
        
        # اگر سشن وجود نداره، از فایل استفاده کن
        if not os.path.exists(session_file):
            print(f"❌ سشن برای {self.phone} وجود ندارد!")
            update_user_status(self.user_id, 'error', {'error': 'سشن وجود ندارد'})
            return
        
        try:
            self.client = TelegramClient(session_file, API_ID, API_HASH)
            self.client.start()
            
            me = self.client.get_me()
            
            print(f"✅ کاربر {me.first_name} (@{me.username}) متصل شد!")
            update_user_status(self.user_id, 'active', {'username': me.username})
            
            ACTIVE_SESSIONS[self.user_id] = {'client': self.client, 'bot': self}
            self.running = True
            
            group = self.client.get_entity(self.group_link)
            self.group_id = group.id
            
            self.client.send_message(self.group_id, "🔥 ماینر اتومات روشن شد!")
            self.main_loop()
            
        except Exception as e:
            print(f"❌ خطا برای کاربر {self.user_id}: {e}")
            update_user_status(self.user_id, 'error', {'error': str(e)})
    
    def main_loop(self):
        time.sleep(5)
        counter = 0
        while self.running:
            try:
                word = random.choice(KEYWORDS)
                self.client.send_message(self.group_id, word)
                counter += 1
                if counter % 5 == 0:
                    self.client.send_message(self.group_id, "فنر")
                
                delay = random.choice(DELAYS) + random.randint(-30, 60)
                delay = max(240, delay)
                time.sleep(delay)
                
            except Exception as e:
                print(f"❌ خطا در حلقه: {e}")
                time.sleep(60)

# ========== اجراکننده ==========
def start_user_bot(user_id, data):
    bot = UserBot(user_id, data)
    bot.start()

def watch_for_new_users():
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

def run_bot():
    print("🚀 ربات اصلی شروع شد...")
    
    os.makedirs(SESSIONS_DIR, exist_ok=True)
    
    threading.Thread(target=watch_for_new_users, daemon=True).start()
    
    users = load_users()
    for user_id, data in users.items():
        if data.get('status') == 'active':
            print(f"🔄 راه‌اندازی مجدد برای {data.get('phone')}")
            threading.Thread(target=start_user_bot, args=(user_id, data)).start()
            time.sleep(2)
    
    print("✅ ربات آماده است!")

if __name__ == "__main__":
    run_bot()
