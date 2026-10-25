import time
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# --- THAY ĐOẠN MÃ DƯỚI ĐÂY BẰNG TOKEN CỦA BẠN NHẬN TỪ BOTFATHER ---
TOKEN = "8959971493:AAEhhwhl2Fl-BEfm_XWPSI6dip4wN6nCqTE"

def get_tiktok_video_url(tiktok_url):
    try:
        api_url = f"https://www.tikwm.com/api/?url={tiktok_url}"
        response = requests.get(api_url, timeout=10).json()
        if response.get("code") == 0:
            return response["data"]["play"]
    except Exception as e:
        print(f"Lỗi gọi API: {e}")
    return None

async def handle_tiktok_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    text = message.text or ""

    if "tiktok.com" in text:
        start_time = time.time()
        words = text.split()
        link = next((w for w in words if "tiktok.com" in w), None)

        if link:
            user = message.from_user
            user_name = user.full_name if user else "Người dùng"
            video_url = get_tiktok_video_url(link)

            if video_url:
                elapsed_time = round(time.time() - start_time, 2)
                caption_text = (
                    f"⚡️ **Đã lấy thành công video no watermark cho bạn !** ✨\n\n"
                    f"👤 **User:** {user_name}\n"
                    f"✨ **Tải video no watermark siêu nhanh!** ⚡️ [{elapsed_time}s]"
                )
                await message.reply_video(
                    video=video_url,
                    caption=caption_text,
                    parse_mode="Markdown"
                )
            else:
                await message.reply_text("❌ Không thể lấy video TikTok này, vui lòng thử lại sau!")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_tiktok_link))
    print("🤖 Bot TikTok đang chạy trên Cloud...")
    app.run_polling()
