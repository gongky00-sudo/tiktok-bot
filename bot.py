import time
import os
import random
import requests
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InputMediaPhoto
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
import yt_dlp

# --- WEB SERVER ẢO DUY TRÌ GÓI FREE TRÊN RENDER ---
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive and running!")

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHandler)
    server.serve_forever()

threading.Thread(target=run_web_server, daemon=True).start()
# ----------------------------------------------------

# --- LUỒNG TỰ ĐỘNG DỌN CACHE 30 PHÚT MỘT LẦN ---
def periodic_cache_cleaner():
    while True:
        # 1800 giây = đúng 30 phút tự động dọn rác ngầm
        time.sleep(1800) 
        try:
            if os.path.exists("downloads"):
                for file in os.listdir("downloads"):
                    file_path = os.path.join("downloads", file)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                print("🧹 [Hệ thống ngầm] Đã tự động dọn sạch thư mục cache sau 30 phút!")
        except Exception as e:
            print(f"Lỗi dọn cache định kỳ: {e}")

threading.Thread(target=periodic_cache_cleaner, daemon=True).start()
# ---------------------------------------

TOKEN = "8959971493:AAEhhwhl2Fl-BEfm_XWPSI6dip4wN6nCqTE"

ERROR_MESSAGES = [
    "🛰️ Đường dẫn này đang bị mã hóa riêng tư quá chặt. Bạn thử gửi link TikTok hoặc Reels khác nhé!",
    "⚡ Bot đã cố gắng bóc tách nhưng bất thành trước tường lửa của nền tảng này. Hãy thử link khác nha bạn!",
    "🎯 Link này hiện không thể truy cập từ máy chủ cloud. Đổi gió sang video ngắn khác giúp mình nhé!",
    "🌀 Gặp chút trở ngại với định dạng link này. Bạn gửi lại link công khai khác để bot chiến tiếp nào!"
]

def clean_cache_folder():
    try:
        if os.path.exists("downloads"):
            for file in os.listdir("downloads"):
                file_path = os.path.join("downloads", file)
                if os.path.isfile(file_path):
                    os.remove(file_path)
    except Exception as e:
        print(f"Lỗi dọn cache ngầm: {e}")

async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        message = update.effective_message
        text = message.text or ""

        supported_domains = ["tiktok.com", "instagram.com", "facebook.com", "fb.watch"]
        if not any(domain in text for domain in supported_domains):
            return

        clean_cache_folder()

        sent_msg = await message.reply_text("🔄 Đang phân tích dữ liệu, chờ chút xíu nhé...")
        start_time = time.time()
        
        words = text.split()
        link = next((w for w in words if any(d in w for d in supported_domains)), None)
        if not link:
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=sent_msg.message_id)
            return

        user = message.from_user
        user_name = user.full_name if user else "Người dùng"
        
        # 1. XỬ LÝ TIKTOK
        if "tiktok.com" in link:
            try:
                api_url = f"https://www.tikwm.com/api/?url={link}&hd=1"
                res = requests.get(api_url, timeout=15).json()
                if res.get("code") == 0:
                    data = res.get("data", {})
                    elapsed = round(time.time() - start_time, 2)
                    
                    images = data.get("images")
                    if images:
                        media_group = [InputMediaPhoto(media=img_url) for img_url in images[:10]]
                        if media_group:
                            await message.reply_media_group(media=media_group)
                            await message.reply_text(
                                f"🎨 **Tải thành công bộ ảnh/live photo TikTok (Full HD)!**\n👤 {user_name} ⏱️ `[{elapsed}s]`",
                                parse_mode="Markdown"
                            )
                            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=sent_msg.message_id)
                            return
                    
                    video_url = data.get("hdplay") or data.get("play")
                    if video_url:
                        await message.reply_video(
                            video=video_url, 
                            caption=f"🎬 **Tải video TikTok Full HD thành công!**\n👤 {user_name} ⏱️ `[{elapsed}s]`", 
                            parse_mode="Markdown"
                        )
                        await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=sent_msg.message_id)
                        return
            except Exception as tik_err:
                print(f"Lỗi TikTok API phụ: {tik_err}")

        # 2. XỬ LÝ INSTAGRAM & FACEBOOK BẰNG YT-DLP
        ydl_opts = {
            'format': 'best',
            'outtmpl': 'downloads/%(id)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
            'geo_bypass': True,
            'nocheckcertificate': True,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
            },
        }
        
        filename = None
        try:
            os.makedirs("downloads", exist_ok=True)
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(link, download=True)
                filename = ydl.prepare_filename(info)
                if not os.path.exists(filename):
                    base, _ = os.path.splitext(filename)
                    for ext in ['.mp4', '.mkv', '.webm', '.jpg', '.png']:
                        if os.path.exists(base + ext):
                            filename = base + ext
                            break
        except Exception as ydl_err:
            print(f"Lỗi yt-dlp chi tiết: {ydl_err}")

        if filename and os.path.exists(filename):
            elapsed =
