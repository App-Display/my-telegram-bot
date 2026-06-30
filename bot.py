import os
import re
import logging
import tempfile

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from yt_dlp import YoutubeDL

# ------------------- الإعدادات -------------------
# تأكد من إضافة BOT_TOKEN في إعدادات البيئة (Environment Variables) في Railway
TOKEN = os.environ.get("BOT_TOKEN")
MAX_FILESIZE_MB = 49 

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

URL_REGEX = re.compile(r"https?://\S+")

# ------------------- دالة التحميل (المحرك المحسن) -------------------
def download_video(url: str, out_dir: str) -> str:
    """يحمّل الفيديو مع محاكاة المتصفح لتجنب الحظر."""
    ydl_opts = {
        "outtmpl": os.path.join(out_dir, "%(id)s.%(ext)s"),
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "merge_output_format": "mp4",
        "noplaylist": True,
        "quiet": True,
        "max_filesize": MAX_FILESIZE_MB * 1024 * 1024,
        
        # 1. تفعيل الكوكيز (يجب أن يكون الملف موجوداً في المجلد)
        "cookiefile": "cookies.txt", 
        
        # 2. الهيدرز الاحترافي لمحاكاة المتصفح
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        },
        
        # 3. التأخير الذكي لتجنب الحظر السريع
        "sleep_interval": 3,
        "max_sleep_interval": 8,
        "geo_bypass": True,
    }
    
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        # التأكد من المسار
        if not os.path.exists(filename):
            base, _ = os.path.splitext(filename)
            filename = base + ".mp4"
        return filename

# ------------------- معالجات الأوامر -------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 أهلاً بك في بوت التحميل الاحترافي.\nأرسل لي أي رابط وسأقوم بتحميله فوراً!")

# ------------------- معالج الروابط -------------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or ""
    match = URL_REGEX.search(text)
    if not match:
        return

    url = match.group(0)
    status_msg = await update.message.reply_text("⏳ جاري المعالجة (محاكاة متصفح)...")

    try:
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = download_video(url, tmp_dir)
            
            await status_msg.edit_text("📤 جاري الرفع لتليجرام...")
            with open(file_path, "rb") as f:
                await update.message.reply_video(video=f, caption="✅ تم التحميل بنجاح!")
            await status_msg.delete()

    except Exception as e:
        logger.error("Download error: %s", e)
        await status_msg.edit_text(f"❌ فشل التحميل.\nالسبب: {str(e)[:50]}...\nتأكد من تحديث ملف cookies.txt.")

# ------------------- تشغيل البوت -------------------
def main():
    if not TOKEN:
        raise SystemExit("❌ خطأ: يرجى ضبط متغير البيئة BOT_TOKEN.")

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
