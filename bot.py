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
TOKEN = os.environ.get("BOT_TOKEN", "ضع_التوكن_هنا")
MAX_FILESIZE_MB = 49  

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

URL_REGEX = re.compile(r"https?://\S+")

# ------------------- الدوال المساعدة -------------------
def download_video(url: str, out_dir: str) -> str:
    """يحمّل الفيديو من الرابط مع محاكاة المتصفح."""
    
    # الإعدادات المحدثة لتجاوز الحظر
    ydl_opts = {
        "outtmpl": os.path.join(out_dir, "%(id)s.%(ext)s"),
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "merge_output_format": "mp4",
        "noplaylist": True,
        "quiet": True,
        "max_filesize": MAX_FILESIZE_MB * 1024 * 1024,
        # إضافة هوية المتصفح
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        },
        "sleep_interval": 3,
        "max_sleep_interval": 8,
        "geo_bypass": True,
    }

    # التحقق من وجود ملف الكوكيز (السر في استمرار العمل)
    if os.path.exists("cookies.txt"):
        ydl_opts["cookiefile"] = "cookies.txt"
        logger.info("تم العثور على cookies.txt واستخدامه.")
    else:
        logger.warning("لم يتم العثور على cookies.txt! البوت سيحاول التحميل بدون هويات.")

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        if not os.path.exists(filename):
            base, _ = os.path.splitext(filename)
            filename = base + ".mp4"
        return filename

# ------------------- معالجات الأوامر -------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "أهلاً بك 👋\n"
        "أرسل لي رابط فيديو وسأقوم بتحميله لك."
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("فقط أرسل رابط الفيديو وسأتولى الباقي.")

# ------------------- معالج الروابط -------------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or ""
    match = URL_REGEX.search(text)
    if not match:
        await update.message.reply_text("أرسل رابط فيديو صالح.")
        return

    url = match.group(0)
    status_msg = await update.message.reply_text("⏳ جاري المعالجة...")

    try:
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = download_video(url, tmp_dir)
            size_mb = os.path.getsize(file_path) / (1024 * 1024)

            if size_mb > MAX_FILESIZE_MB:
                await status_msg.edit_text(f"⚠️ الفيديو ({size_mb:.1f}MB) كبير جداً.")
                return

            await status_msg.edit_text("📤 جاري الإرسال...")
            with open(file_path, "rb") as f:
                await update.message.reply_video(video=f, caption="تم بنجاح ✅")
            await status_msg.delete()

    except Exception as e:
        logger.error("Download error: %s", e)
        await status_msg.edit_text("❌ تعذر تحميل الفيديو. تأكد من صحة الرابط.")

# ------------------- تشغيل البوت -------------------
def main():
    if TOKEN == "ضع_التوكن_هنا":
        raise SystemExit("خطأ: يرجى وضع التوكن في BOT_TOKEN")

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
