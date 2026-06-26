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
BOT_TOKEN = os.getenv("BOT_TOKEN", "8446745973:AAGRD2tFbSrzB2OFoByvYRHCY1Hp6nluHf0")
bot = telebot.TeleBot(BOT_TOKEN)
DB_FILE = "/tmp/voice_db.json"
model = whisper.load_model("small")

# --- خدمات النظام ---
def run_dummy_server():
    try: http.server.HTTPServer(('', int(os.environ.get("PORT", 8080))), http.server.SimpleHTTPRequestHandler).serve_forever()
    except: pass
threading.Thread(target=run_dummy_server, daemon=True).start()

def load_db():
    if not os.path.exists(DB_FILE): return {"girl_1": {}, "girl_2": {}}
    try:
        with open(DB_FILE, 'r', encoding='utf-8') as f: return json.load(f)
    except: return {"girl_1": {}, "girl_2": {}}

def save_db(db):
    try: with open(DB_FILE, 'w', encoding='utf-8') as f: json.dump(db, f, indent=4, ensure_ascii=False)
    except: pass

# --- تحميل الفيديو والترجمة ---
def download_video_sync(url, cid):
    try:
        ydl_opts = {'format': 'best[ext=mp4]/best', 'outtmpl': f'/tmp/vid_{cid}.mp4', 'quiet': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl: info = ydl.extract_info(url, download=True); return f'/tmp/vid_{cid}.mp4', info.get('title', 'Video')
    except Exception as e: return None, str(e)

def process_translation(v_path, lang):
    audio_p = v_path.replace('.mp4', '.wav')
    subprocess.run(['ffmpeg', '-i', v_path, '-vn', '-acodec', 'pcm_s16le', '-ar', '16000', '-ac', '1', audio_p, '-y'], capture_output=True)
    res = model.transcribe(audio_p, language=lang)
    srt_p = v_path.replace('.mp4', '.srt')
    with open(srt_p, 'w', encoding='utf-8') as f:
        for i, seg in enumerate(res['segments'], 1):
            f.write(f"{i}\n{seg['start']} --> {seg['end']}\n{GoogleTranslator(source=lang, target='ar').translate(seg['text'])}\n\n")
    out_p = v_path.replace('.mp4', '_tr.mp4')
    subprocess.run(['ffmpeg', '-i', v_path, '-vf', f"subtitles={srt_p}", '-c:a', 'copy', out_p, '-y'], capture_output=True)
    return out_p

# --- القائمة الرئيسية ---
@bot.message_handler(commands=['start'])
def start(m):
    welcome_msg = "🤖 أهلاً بك، المطور سيف الدين يرحب بك في البوت الشامل! 🌹"
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("🖼️ رابط صور", callback_data="p_link"),
        types.InlineKeyboardButton("🎥 رابط فيديو", callback_data="v_link"),
        types.InlineKeyboardButton("📥 تحميل فيديو", callback_data="dl_vid"),
        types.InlineKeyboardButton("🎧 قسم الصوتيات", callback_data="v_menu"),
        types.InlineKeyboardButton("🔒 حقن رابط في صورة", callback_data="inject"),
        types.InlineKeyboardButton("🌐 ترجمة فيديو", callback_data="trans_menu")
    )
    bot.send_message(m.chat.id, welcome_msg, reply_markup=kb)

# --- المعالج العام ---
@bot.callback_query_handler(func=lambda c: True)
def query(c):
    cid = c.message.chat.id
    if c.data == "dl_vid": bot.edit_message_text("أرسل رابط التحميل:", cid, c.message.message_id); bot.register_next_step_handler(c.message, dl_p)
    elif c.data == "v_menu": 
        m = types.InlineKeyboardMarkup(); m.add(types.InlineKeyboardButton("الفتاة 1", callback_data="g1"), types.InlineKeyboardButton("الفتاة 2", callback_data="g2")); bot.edit_message_text("اختر المجلد:", cid, c.message.message_id, reply_markup=m)
    elif c.data in ["g1", "g2"]: bot.answer_callback_query(c.id, "أرسل فويس للتحديث"); open(f"/tmp/state_{cid}.txt", "w").write(c.data)
    elif c.data == "trans_menu": 
        m = types.InlineKeyboardMarkup(); m.add(types.InlineKeyboardButton("Fr -> Ar", callback_data="tr:fr"), types.InlineKeyboardButton("En -> Ar", callback_data="tr:en")); bot.edit_message_text("اختر اللغة:", cid, c.message.message_id, reply_markup=m)
    elif c.data.startswith("tr:"): bot.edit_message_text(f"أرسل الفيديو للترجمة ({c.data})", cid, c.message.message_id); open(f"/tmp/tr_{cid}.txt", "w").write(c.data.split(":")[1])
    bot.answer_callback_query(c.id)

def dl_p(m):
    s = bot.reply_to(m, "⏳ جار التحميل..."); p, t = download_video_sync(m.text, m.chat.id)
    if p: bot.send_video(m.chat.id, open(p, 'rb'), caption=t); bot.delete_message(m.chat.id, s.message_id); os.remove(p)

@bot.message_handler(content_types=['voice', 'video'])
def handle_all(m):
    cid = m.chat.id
    if m.voice and os.path.exists(f"/tmp/state_{cid}.txt"):
        with open(f"/tmp/state_{cid}.txt", "r") as f: target = f.read()
        db = load_db(); key = "girl_1" if target == "g1" else "girl_2"; idx = len(db[key]) + 1; db[key][f"مقطع {idx}"] = m.voice.file_id; save_db(db); bot.reply_to(m, "✅ تم الحفظ"); os.remove(f"/tmp/state_{cid}.txt")
    elif m.video and os.path.exists(f"/tmp/tr_{cid}.txt"):
        with open(f"/tmp/tr_{cid}.txt", "r") as f: lang = f.read()
        s = bot.reply_to(m, "⏳ جاري الترجمة..."); path = f"/tmp/{cid}.mp4"; bot.download_file(bot.get_file(m.video.file_id).file_path, path); out = process_translation(path, lang); bot.send_video(cid, open(out, 'rb')); os.remove(path); os.remove(out); os.remove(f"/tmp/tr_{cid}.txt")

bot.polling(none_stop=True)

