"""
فایل اصلی - اجرای همه چیز
"""

import os
import threading
import time
import asyncio
from flask import Flask
import web_panel
import bot_core

# ========== تنظیمات ==========
API_ID = 17187664
API_HASH = 'd6eae2c921342bb71816a980dc11b9f5'

# ========== اجرا ==========
if __name__ == "__main__":
    print("""
    ╔════════════════════════════════════════╗
    ║  🐱 ربات کامل میو                     ║
    ║  پنل ثبت‌نام + ربات اصلی              ║
    ╚════════════════════════════════════════╝
    """)
    
    # ساخت پوشه‌ها
    os.makedirs('sessions', exist_ok=True)
    os.makedirs('templates', exist_ok=True)
    
    # شروع ربات اصلی در پس‌زمینه
    print("🚀 ربات اصلی در حال راه‌اندازی...")
    threading.Thread(target=bot_core.run_bot, daemon=True).start()
    time.sleep(2)
    
    # شروع پنل وب
    print("🌐 پنل وب در حال راه‌اندازی...")
    port = int(os.environ.get('PORT', 10000))
    web_panel.app.run(host='0.0.0.0', port=port, debug=False)
