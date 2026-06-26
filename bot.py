import os
import json
import telebot
from telebot import types
import threading
import http.server
import yt_dlp
import subprocess
import whisper
from deep_translator import GoogleTranslator
from PIL import Image, PngImagePlugin

# --- الإعدادات ---
BOT_TOKEN = os.getenv("BOT_TOKEN", "8128965245:AAGolmLae3ALVga_kcloXCK2zsFRODK4BXc")
bot = telebot.TeleBot(BOT_TOKEN)
DB_FILE = "/tmp/voice_db.json"
model = whisper.load_model("small")

# --- خدمات النظام ---
def run_dummy_server():
    try:
        http.server.HTTPServer(('', int(os.environ.get("PORT", 8080))), http.server.SimpleHTTPRequestHandler).serve_forever()
    except: pass
threading.Thread(target=run_dummy_server, daemon=True).start()

# --- أدوات الترجمة والتحويل ---
def seconds_to_srt(s):
    h, m, s = int(s // 3600), int((s % 3600) // 60), s % 60
    return f"{h:02d}:{m:02d}:{int(s):02d},{int((s%1)*1000):03d}"

def process_translation(video_path, lang):
    audio_path = video_path.replace('.mp4', '.wav')
    subprocess.run(['ffmpeg', '-i', video_path, '-vn', '-acodec', 'pcm_s16le', '-ar', '16000', '-ac', '1', audio_path, '-y'], capture_output=True)
    res = model.transcribe(audio_path, language=lang)
    srt_path = video_path.replace('.mp4', '.srt')
    with open(srt_path, 'w', encoding='utf-8') as f:
        for i, seg in enumerate(res['segments'], 1):
            f.write(f"{i}\n{seconds_to_srt(seg['start'])} --> {seconds_to_srt(seg['end'])}\n{GoogleTranslator(source=lang, target='ar').translate(seg['text'])}\n\n")
    out_path = video_path.replace('.mp4', '_tr.mp4')
    subprocess.run(['ffmpeg', '-i', video_path, '-vf', f"subtitles={srt_path}", '-c:a', 'copy', out_path, '-y'], capture_output=True)
    return out_path

# --- القوائم الرئيسية ---
@bot.message_handler(commands=['start'])
def start(m):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("🖼️ رابط صور", callback_data="p_link"),
        types.InlineKeyboardButton("🎥 رابط فيديو", callback_data="v_link"),
        types.InlineKeyboardButton("📥 تحميل فيديو", callback_data="dl_mode"),
        types.InlineKeyboardButton("🎧 قسم الصوتيات", callback_data="v_menu"),
        types.InlineKeyboardButton("🌐 ترجمة فيديو", callback_data="trans_menu")
    )
    bot.send_message(m.chat.id, "🤖 أهلاً بك يا سيف، القائمة الرئيسية:", reply_markup=kb)

# --- معالجة الأزرار ---
@bot.callback_query_handler(func=lambda c: True)
def query(c):
    cid = c.message.chat.id
    if c.data == "trans_menu":
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton("فرنسي -> عربي", callback_data="tr:fr"),
              types.InlineKeyboardButton("إنجليزي -> عربي", callback_data="tr:en"))
        bot.edit_message_text("اختر لغة الفيديو:", cid, c.message.message_id, reply_markup=m)
    elif c.data.startswith("tr:"):
        bot.edit_message_text(f"أرسل الفيديو الآن ليتم ترجمته من {c.data.split(':')[1]}", cid, c.message.message_id)
        # حفظ حالة المستخدم للترجمة
        with open(f"/tmp/state_{cid}.txt", "w") as f: f.write(c.data)
    # ... (باقي كود الصوتيات والتحميل هنا كما في النسخة السابقة) ...
    bot.answer_callback_query(c.id)

# --- معالجة الملفات (فيديو للترجمة) ---
@bot.message_handler(content_types=['video'])
def handle_docs(m):
    cid = m.chat.id
    if os.path.exists(f"/tmp/state_{cid}.txt"):
        with open(f"/tmp/state_{cid}.txt", "r") as f: lang = f.read().split(":")[1]
        s = bot.reply_to(m, "⏳ جاري المعالجة والترجمة... قد يأخذ وقتاً")
        path = f"/tmp/{cid}.mp4"
        bot.download_file(bot.get_file(m.video.file_id).file_path, path)
        out = process_translation(path, lang)
        bot.send_video(cid, open(out, 'rb'), caption="✅ تم تعريب الفيديو!")
        os.remove(path); os.remove(out)
        os.remove(f"/tmp/state_{cid}.txt")
