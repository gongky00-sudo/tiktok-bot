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

TOKEN = "8959971493:AAEhhwhl2Fl-BEfm_XWPSI6dip4wN6nCqTE"

# Danh sách câu báo lỗi mới, thay đổi liên tục và sinh động hơn
ERROR_MESSAGES = [
    "🛰️ Trạm trung gian đang bận né trạm kiểm soát của Instagram. Bạn thử gửi lại đường link Reels khác giúp mình nha!",
    "⚡ Đã thử móc nối qua cổng phụ nhưng đường truyền Instagram đang khóa chặt. Đổi gió sang link TikTok hoặc bài viết khác xem sao bạn ơi!",
    "🎯 Hướng tiếp cận này tạm thời bị tường lửa giữ lại. Bạn hãy thử gửi một chiếc link video ngắn khác để bot mượt mà chiến tiếp nhé!",
    "🌀 Link này có vẻ được bảo vệ cực kỳ gắt gao. Hãy thử qua một đường dẫn công khai khác để bot dễ dàng xử lý hơn nào!"
]

async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    text = message.text or ""

    supported_domains = ["tiktok.com", "instagram.com", "facebook.com", "fb.watch"]
    if any(domain in text for domain in supported_domains):
        sent_msg = await message.reply_text("🔄 Đang chuyển hướng qua trạm trung gian để bóc tách, chờ một tí nhé...")
        
        start_time = time.time()
        words = text.split()
        link = next((w for w in words if any(d in w for d in supported_domains)), None)

        if link:
            user = message.from_user
            user_name = user.full_name if user else "Người dùng"
            
            # 1. XỬ LÝ TIKTOK (Siêu tốc, hỗ trợ Video HD & Live Photo / Album ảnh)
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
                                    f"🎨 **Đã tóm gọn bộ ảnh/live photo TikTok (Full HD)!**\n👤 {user_name} ⏱️ `[{elapsed}s]`",
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
                except Exception as e:
                    print(f"Lỗi TikTok API: {e}")

            # 2. XỬ LÝ INSTAGRAM & FACEBOOK (Tích hợp cơ chế giả lập trạm trung gian nâng cao)
            ydl_opts = {
                'format': 'best',
                'outtmpl': 'downloads/%(id)s.%(ext)s',
                'quiet': True,
                'no_warnings': True,
                'geo_bypass': True,
                'nocheckcertificate': True,
                'extractor_args': {'instagram': {'max_comments': 0}},
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Referer': 'https://www.instagram.com/',
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
                caption_text = f"✨ **Bóc tách dữ liệu thành công!**\n👤 {user_name} ⏱️ `[{elapsed}s]`"
                
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
                # Lấy ngẫu nhiên một câu thông báo lỗi mới hoàn toàn
                random_error = random.choice(ERROR_MESSAGES)
                await message.reply_text(random_error)

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_media))
    print("🤖 Bot trạm trung gian đa năng đang hoạt động...")
    app.run_polling()
