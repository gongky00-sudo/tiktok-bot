import time
import os
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

TOKEN = "8959971493:AAEhhwhl2Fl-BEfm_XWPSI6dip4wN6nCqTE"  # Thay token bot của bạn vào đây

async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    text = message.text or ""

    supported_domains = ["tiktok.com", "instagram.com", "facebook.com", "fb.watch"]
    if any(domain in text for domain in supported_domains):
        sent_msg = await message.reply_text("⏳ Đang vượt tường lửa phân tích link, vui lòng đợi chốc lát...")
        
        start_time = time.time()
        words = text.split()
        link = next((w for w in words if any(d in w for d in supported_domains)), None)

        if link:
            user = message.from_user
            user_name = user.full_name if user else "Người dùng"
            
            # 1. XỬ LÝ TIKTOK (Dùng API chính chủ cực kỳ ổn định)
            if "tiktok.com" in link:
                try:
                    api_url = f"https://www.tikwm.com/api/?url={link}&hd=1"
                    res = requests.get(api_url, timeout=15).json()
                    if res.get("code") == 0:
                        data = res.get("data", {})
                        elapsed = round(time.time() - start_time, 2)
                        
                        # Xử lý dạng album ảnh / live photo
                        images = data.get("images")
                        if images:
                            media_group = [InputMediaPhoto(media=img_url) for img_url in images[:10]]
                            if media_group:
                                await message.reply_media_group(media=media_group)
                                await message.reply_text(
                                    f"✨ **Tải thành công bộ ảnh TikTok (Full HD)!**\n👤 {user_name} ⏱️ `[{elapsed}s]`",
                                    parse_mode="Markdown"
                                )
                                await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=sent_msg.message_id)
                                return
                        
                        # Xử lý dạng video
                        video_url = data.get("hdplay") or data.get("play")
                        if video_url:
                            await message.reply_video(
                                video=video_url, 
                                caption=f"✨ **Tải video TikTok Full HD thành công!**\n👤 {user_name} ⏱️ `[{elapsed}s]`", 
                                parse_mode="Markdown"
                            )
                            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=sent_msg.message_id)
                            return
                except Exception as e:
                    print(f"Lỗi TikTok API: {e}")

            # 2. XỬ LÝ INSTAGRAM & FACEBOOK (Đã vá lỗi bằng bộ giả lập trình duyệt User-Agent)
            ydl_opts = {
                'format': 'bestvideo+bestaudio/best/best',
                'outtmpl': 'downloads/%(id)s.%(ext)s',
                'quiet': True,
                'no_warnings': True,
                'geo_bypass': True,
                'nocheckcertificate': True,
                # Vá lỗi chặn IP cloud bằng cách giả lập trình duyệt thật của người dùng
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Sec-Fetch-Mode': 'navigate',
                },
                'merge_output_format': 'mp4',
            }
            
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

                elapsed = round(time.time() - start_time, 2)
                caption_text = f"✨ **Tải nội dung Full HD thành công!**\n👤 {user_name} ⏱️ `[{elapsed}s]`"
                
                if os.path.exists(filename):
                    with open(filename, 'rb') as f:
                        if filename.endswith(('.jpg', '.png', '.jpeg', '.webp')):
                            await message.reply_photo(photo=f, caption=caption_text, parse_mode="Markdown")
                        else:
                            await message.reply_video(video=f, caption=caption_text, parse_mode="Markdown")
                    os.remove(filename)
                
                await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=sent_msg.message_id)
                
            except Exception as e:
                print(f"Lỗi chi tiết yt-dlp: {e}")
                await message.reply_text("❌ Nền tảng này đang tạm khóa kết nối từ máy chủ. Bạn hãy thử lại sau ít phút hoặc kiểm tra xem link có bị đổi định dạng không nhé!")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_media))
    print("🤖 Bot đa nền tảng bản vá v2 đang chạy...")
    app.run_polling()
