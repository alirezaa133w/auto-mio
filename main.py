"""
ربات اصلی میو - روی Render اجرا میشه
"""

import asyncio
import json
import os
import random
import re
from datetime import datetime
from telethon import TelegramClient, events

# ========== تنظیمات ==========
API_ID = 17187664
API_HASH = 'd6eae2c921342bb71816a980dc11b9f5'

USERS_FILE = 'users.json'
SESSIONS_DIR = 'sessions/'
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

# ========== کلاس ربات کاربر ==========
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
            print(f"❌ خطا برای کاربر {self.user_id}: {e}")
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

# ========== واتچر ==========
async def watch_for_new_users():
    while True:
        try:
            users = load_users()
            for user_id, data in users.items():
                if data.get('status') == 'pending' and user_id not in ACTIVE_SESSIONS:
                    print(f"🆕 کاربر جدید: {data.get('phone')}")
                    bot = UserBot(user_id, data)
                    asyncio.create_task(bot.start())
                    await asyncio.sleep(3)
            await asyncio.sleep(10)
        except Exception as e:
            print(f"⚠️ واتچر: {e}")
            await asyncio.sleep(30)

# ========== تابع اصلی ==========
async def main():
    ensure_files()
    print("🚀 ربات اصلی شروع شد...")
    
    users = load_users()
    for user_id, data in users.items():
        if data.get('status') == 'active':
            bot = UserBot(user_id, data)
            asyncio.create_task(bot.start())
            await asyncio.sleep(2)
    
    asyncio.create_task(watch_for_new_users())
    print("✅ آماده است!")
    await asyncio.Event().wait()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 خداحافظ!")
    except Exception as e:
        print(f"❌ خطا: {e}")
