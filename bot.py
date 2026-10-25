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

# Token của bạn đã được gắn sẵn
TOKEN = "8959971493:AAEhhwhl2Fl-BEfm_XWPSI6dip4wN6nCqTE"

# Danh sách câu báo lỗi xoay vòng khi gặp link khó nhằn
ERROR_MESSAGES = [
    "🚧 Instagram đang bật khiên bảo vệ quá cứng với máy chủ đám mây. Bạn hãy thử gửi link dạng Reels hoặc bài viết đơn lẻ khác xem sao nhé!",
    "🛡️ Ôi, hệ thống phòng thủ của Meta đã chặn yêu cầu này từ cloud IP. Thử lại bằng một đường link bài đăng khác giúp mình nha!",
    "⚠️ Link này đang bị tường lửa từ chối truy cập trực tiếp. Bạn có thể đổi sang link video TikTok hoặc Reels khác để bot múa trơn tru hơn nhé!",
    "🛑 Tạm thời chưa bóc tách được link này do chính sách bảo mật riêng tư của nền tảng. Hãy thử gửi link công khai dạng video ngắn xem sao bạn nhé!"
]

async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    text = message.text or ""

    supported_domains = ["tiktok.com", "instagram.com", "facebook.com", "fb.watch"]
    if any(domain in text for domain in supported_domains):
        sent_msg = await message.reply_text("⚡ Đang kích hoạt chế độ xuyên thủng tường lửa, chờ xíu nha...")
        
        start_time = time.time()
        words = text.split()
        link = next((w for w in words if any(d in w for d in supported_domains)), None)

        if link:
            user = message.from_user
            user_name = user.full_name if user else "Người dùng"
            
            # 1. XỬ LÝ TIKTOK (Siêu tốc độ, hỗ trợ Full HD & Live Photo / Album ảnh)
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
                                    f"✨ **Tải thành công bộ ảnh/live photo TikTok (Full HD)!**\n👤 {user_name} ⏱️ `[{elapsed}s]`",
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

            # 2. XỬ LÝ INSTAGRAM & FACEBOOK (Nâng cấp tối đa bộ giả lập thiết bị di động)
            ydl_opts = {
                'format': 'best',
                'outtmpl': 'downloads/%(id)s.%(ext)s',
                'quiet': True,
                'no_warnings': True,
                'geo_bypass': True,
                'nocheckcertificate': True,
                'extractor_args': {'instagram': {'max_comments': 0}},
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.55 (KHTML, like Gecko) Mobile/15E148 Instagram 313.0.0.31.110',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                    'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
                    'Sec-Fetch-Site': 'none',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-User': '?1',
                    'Sec-Fetch-Dest': 'document',
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
                # Lấy ngẫu nhiên một câu thông báo lỗi khác nhau mỗi khi lỗi xảy ra
                random_error = random.choice(ERROR_MESSAGES)
                await message.reply_text(random_error)

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_media))
    print("🤖 Bot đa nền tảng bản tối ưu mạnh mẽ đang chạy...")
    app.run_polling()
