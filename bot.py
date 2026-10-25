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

TOKEN = "YOUR_BOT_TOKEN_HERE"  # Thay token bot của bạn vào đây

async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    text = message.text or ""

    supported_domains = ["tiktok.com", "instagram.com", "facebook.com", "fb.watch"]
    if any(domain in text for domain in supported_domains):
        sent_msg = await message.reply_text("⏳ Đang xử lý yêu cầu, vui lòng đợi chốc lát...")
        
        start_time = time.time()
        words = text.split()
        link = next((w for w in words if any(d in w for d in supported_domains)), None)

        if link:
            user = message.from_user
            user_name = user.full_name if user else "Người dùng"
            
            # 1. XỬ LÝ TIKTOK (Siêu mượt, hỗ trợ cả Video HD và Album ảnh/Live Photo)
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
                                    f"✨ **Tải thành công bộ ảnh TikTok (Full HD)!**\n👤 {user_name} ⏱️ `[{elapsed}s]`",
                                    parse_mode="Markdown"
                                )
                                await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=sent_msg.message_id)
                                return
                        
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

            # 2. XỬ LÝ INSTAGRAM & FACEBOOK (Tối ưu hóa bộ giả lập để giảm thiểu bị chặn)
            ydl_opts = {
                'format': 'best',
                'outtmpl': 'downloads/%(id)s.%(ext)s',
                'quiet': True,
                'no_warnings': True,
                'geo_bypass': True,
                'nocheckcertificate': True,
                'extractor_args': {'instagram': {'max_comments': 0}},
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.55 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
                    'Accept-Language': 'en-US,en;q=0.9',
                },
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
                caption_text = f"✨ **Tải nội dung thành công!**\n👤 {user_name} ⏱️ `[{elapsed}s]`"
                
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
                # Thông báo chi tiết rõ ràng hơn cho người dùng khi gặp link trang cá nhân / bị chặn
                await message.reply_text(
                    "⚠️ **Instagram đang tạm chặn kết nối từ máy chủ đám mây đối với link này!**\n\n"
                    "💡 *Mẹo:* Các link **Trang cá nhân (Profile)**, **Story** hoặc **Highlights** của Instagram yêu cầu phải đăng nhập tài khoản mới xem được nên bot miễn phí trên cloud không thể cào trực tiếp được. Bạn hãy gửi link **Reels cụ thể** hoặc **Bài viết dạng video/ảnh đơn lẻ** thì tỷ lệ tải thành công sẽ cao hơn rất nhiều nhé!"
                )

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_media))
    print("🤖 Bot đa nền tảng đang chạy...")
    app.run_polling()
