import logging
import json
import random
import os
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = "8592051460:AAFsgIBemMykOZonfhgKG6Sb7UyVOGvlgMM"
GROUP_ID = -1007958087186
SPAWN_INTERVAL = 30 * 60

ANIME_CHARACTERS = [
    {"name": "Naruto Uzumaki", "anime": "Naruto"},
    {"name": "Sasuke Uchiha", "anime": "Naruto"},
    {"name": "Luffy", "anime": "One Piece"},
    {"name": "Zoro", "anime": "One Piece"},
    {"name": "Nami", "anime": "One Piece"},
    {"name": "Sanji", "anime": "One Piece"},
    {"name": "Ichigo Kurosaki", "anime": "Bleach"},
    {"name": "Rukia Kuchiki", "anime": "Bleach"},
    {"name": "Tanjiro Kamado", "anime": "Demon Slayer"},
    {"name": "Nezuko Kamado", "anime": "Demon Slayer"},
    {"name": "Deku", "anime": "My Hero Academia"},
    {"name": "Bakugo", "anime": "My Hero Academia"},
    {"name": "Todoroki", "anime": "My Hero Academia"},
    {"name": "Goku", "anime": "Dragon Ball Z"},
    {"name": "Vegeta", "anime": "Dragon Ball Z"},
    {"name": "Saitama", "anime": "One Punch Man"},
    {"name": "Genos", "anime": "One Punch Man"},
    {"name": "Eren Yeager", "anime": "Attack on Titan"},
    {"name": "Mikasa Ackerman", "anime": "Attack on Titan"},
    {"name": "Levi Ackerman", "anime": "Attack on Titan"},
]

class Database:
    def __init__(self, filename="data.json"):
        self.filename = filename
        self.data = self.load()
    
    def load(self):
        if os.path.exists(self.filename):
            with open(self.filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "users": {},
            "current_character": None,
            "last_spawn_time": 0
        }
    
    def save(self):
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
    
    def get_user(self, user_id):
        user_id = str(user_id)
        if user_id not in self.data["users"]:
            self.data["users"][user_id] = {
                "username": "",
                "coins": 0,
                "xp": 0,
                "level": 0,
                "collection": []
            }
            self.save()
        return self.data["users"][user_id]
    
    def add_character(self, user_id, character_name, anime_name):
        user = self.get_user(user_id)
        user["collection"].append({
            "name": character_name,
            "anime": anime_name,
            "caught_at": datetime.now().isoformat()
        })
        self.save()
    
    def add_coins(self, user_id, amount):
        user = self.get_user(user_id)
        user["coins"] += amount
        self.save()
    
    def add_xp(self, user_id, amount):
        user = self.get_user(user_id)
        user["xp"] += amount
        
        while user["xp"] >= 100 and user["level"] < 30:
            user["xp"] -= 100
            user["level"] += 1
        
        self.save()
    
    def set_current_character(self, character):
        self.data["current_character"] = character
        self.data["last_spawn_time"] = datetime.now().isoformat()
        self.save()
    
    def get_current_character(self):
        return self.data["current_character"]
    
    def clear_current_character(self):
        self.data["current_character"] = None
        self.save()
    
    def get_leaderboard(self, limit=10):
        users = list(self.data["users"].items())
        users.sort(key=lambda x: (x[1]["level"], x[1]["xp"]), reverse=True)
        return users[:limit]

db = Database()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = db.get_user(update.effective_user.id)
    user["username"] = update.effective_user.username or update.effective_user.first_name
    db.save()
    
    welcome_text = """🎮 خوش آمدید به AimirAnimeBot! 🎮

📋 چطور کار می‌کند:
• هر 30 دقیقه یک شخصیت انیمه spawn می‌شود
• اول کسی که نام صحیح را بگوید، شخصیت را می‌گیرد
• هر گرفتن: 50 💰 + 35 ⭐

🎯 دستورات:
/stats - آمار شخصی
/collection - کالکشن شما
/top - جدول رتبه‌بندی
/help - راهنما

بازی رو شروع کنید! 🚀"""
    
    await update.message.reply_text(welcome_text)

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = db.get_user(update.effective_user.id)
    
    stats_text = f"""📊 آمار شما:

👤 نام: {user['username']}
💰 Coins: {user['coins']}
⭐ XP: {user['xp']}/100
🎖️ Level: {user['level']}/30
🎁 کالکشن: {len(user['collection'])} شخصیت"""
    
    await update.message.reply_text(stats_text)

async def collection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = db.get_user(update.effective_user.id)
    
    if not user["collection"]:
        await update.message.reply_text("📭 هنوز شخصیتی را نگرفته‌اید!")
        return
    
    collection_text = "🎁 کالکشن شما:\n\n"
    for i, char in enumerate(user["collection"], 1):
        collection_text += f"{i}. {char['name']} - {char['anime']}\n"
    
    await update.message.reply_text(collection_text)

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    top_users = db.get_leaderboard(10)
    
    if not top_users:
        await update.message.reply_text("🏆 هنوز کسی بازی نکرده!")
        return
    
    leaderboard_text = "🏆 جدول رتبه‌بندی:\n\n"
    for i, (user_id, user_data) in enumerate(top_users, 1):
        leaderboard_text += f"{i}. {user_data['username']} - Level {user_data['level']} | Coins: {user_data['coins']}\n"
    
    await update.message.reply_text(leaderboard_text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """❓ راهنمای بازی:

🎮 چطور شخصیت بگیرم؟
هر 30 دقیقه یک شخصیت انیمه به گروپ فرستاده می‌شود.
شما باید اول نام صحیح را پیام دهید!

💰 جوایز:
هر شخصیت: 50 Coins + 35 XP

📊 سیستم Level:
100 XP = 1 Level
حداکثر Level: 30

🎁 دستورات:
/stats - آمار شخصی
/collection - کالکشن
/top - رتبه‌بندی
/help - این راهنما

🎯 نکات مهم:
• تنها اول کسی که بگوید، شخصیت می‌گیرد
• اسم باید دقیق باشد
• هرچه بیشتر بازی کنی، بیشتر reward می‌گیری

خیلی سریع باشید! ⚡"""
    
    await update.message.reply_text(help_text)

async def spawn_character(context: ContextTypes.DEFAULT_TYPE):
    character = random.choice(ANIME_CHARACTERS)
    db.set_current_character(character)
    
    message_text = f"""🎬 شخصیت جدید spawn شد!

کدام شخصیت است؟
نام را بنویس!"""
    
    try:
        await context.bot.send_message(
            chat_id=GROUP_ID,
            text=message_text
        )
        logger.info(f"Character spawned: {character['name']}")
    except Exception as e:
        logger.error(f"Error spawning character: {e}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.id != GROUP_ID:
        return
    
    current_character = db.get_current_character()
    if not current_character:
        return
    
    user_message = update.message.text.strip()
    correct_name = current_character["name"].lower()
    
    if user_message.lower() == correct_name:
        user_id = update.effective_user.id
        username = update.effective_user.username or update.effective_user.first_name
        
        db.add_character(user_id, current_character["name"], current_character["anime"])
        db.add_coins(user_id, 50)
        db.add_xp(user_id, 35)
        db.get_user(user_id)["username"] = username
        db.save()
        
        user = db.get_user(user_id)
        
        reward_text = f"""✅ تبریک {username}! ✅

🎁 شخصیت: {current_character['name']}
🎬 انیمه: {current_character['anime']}

💰 +50 Coins (کل: {user['coins']})
⭐ +35 XP (کل: {user['xp']}/100)
🎖️ Level: {user['level']}/30"""
        
        await update.message.reply_text(reward_text)
        db.clear_current_character()

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("collection", collection))
    app.add_handler(CommandHandler("top", leaderboard))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    app.job_queue.run_repeating(spawn_character, interval=SPAWN_INTERVAL, first=10)
    
    logger.info("Bot started successfully!")
    app.run_polling()

if __name__ == '__main__':
    main()
