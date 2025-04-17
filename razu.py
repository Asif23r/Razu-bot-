import telebot
import json
import os
from telebot import types

bot = telebot.TeleBot("YOUR_BOT_TOKEN")  # ← Bot token yahan daalo
admin_id = 1234567890  # ← Apna Telegram ID yahan daalo

# Load or create users.json
if os.path.exists("users.json"):
    with open("users.json", "r") as f:
        users = json.load(f)
else:
    users = {}

# Save function
def save_users():
    with open("users.json", "w") as f:
        json.dump(users, f, indent=2)

# Check if user is blocked
def is_blocked(user_id):
    return users.get(user_id, {}).get("blocked", False)

# /start
@bot.message_handler(commands=["start"])
def start(message):
    user_id = str(message.from_user.id)
    username = message.from_user.username or "NoUsername"

    if user_id not in users:
        users[user_id] = {
            "username": username,
            "points": 5,
            "referrals": [],
            "total_notes": 0,
            "blocked": False
        }
        save_users()

    if is_blocked(user_id):
        bot.reply_to(message, "❌ Tum blocked ho.")
        return

    bot.reply_to(message,
        "👋 Welcome to Paid Notes Bot!\n\n"
        "🎁 You got 5 free points!\n"
        "📚 Use /notes to get notes.\n\n"
        "💰 Commands:\n"
        "/buy – Buy points\n"
        "/points – Check balance\n"
        "/help – See all user commands\n\n"
        "❗Note: Misuse will result in block!"
    )

# Notify admin when a new user joins
@bot.message_handler(content_types=["new_chat_members"])
def new_user(message):
    for new_user in message.new_chat_members:
        bot.send_message(admin_id, f"New user joined: {new_user.username or 'NoUsername'} (ID: {new_user.id})")

# /help
@bot.message_handler(commands=["help"])
def help_cmd(message):
    if is_blocked(str(message.from_user.id)):
        return bot.reply_to(message, "❌ Tum blocked ho.")
    bot.reply_to(message,
        "📌 *User Commands:*\n"
        "/start – Register & get points\n"
        "/notes – Use 1 point to get note\n"
        "/buy – Buy more points\n"
        "/points – Check your points\n"
        "/help – Show commands",
        parse_mode="Markdown"
    )

# /points
@bot.message_handler(commands=["points"])
def points(message):
    user_id = str(message.from_user.id)
    if is_blocked(user_id):
        return bot.reply_to(message, "❌ Tum blocked ho.")
    if user_id in users:
        bot.reply_to(message, f"💎 Tumhare paas {users[user_id]['points']} points hain.")
    else:
        bot.reply_to(message, "❗Pehle /start bhejo.")

# /notes
@bot.message_handler(commands=["notes"])
def notes(message):
    user_id = str(message.from_user.id)
    if user_id not in users or is_blocked(user_id):
        bot.reply_to(message, "❌ Tum blocked ho ya registered nahi ho.")
        return

    if users[user_id]["points"] > 0:
        users[user_id]["points"] -= 1
        users[user_id]["total_notes"] += 1
        save_users()
        bot.reply_to(message, "📝 Yeh raha tumhara note:\n\n[Note content here]")
    else:
        bot.reply_to(message, "😓 Tumhare points khatam ho gaye hain. Use /buy")

# /buy
@bot.message_handler(commands=["buy"])
def buy(message):
    user_id = str(message.from_user.id)
    username = message.from_user.username or "NoUsername"

    if is_blocked(user_id):
        return bot.reply_to(message, "❌ Tum blocked ho.")
    
    bot.reply_to(message,
        "💰 *Buy Points:*\n\n"
        "₹20 = 20 Points\n"
        "UPI ID: raaz@upi\n\n"
        "Payment ke baad screenshot bhejo.",
        parse_mode="Markdown"
    )
    bot.send_message(admin_id, f"📥 Buy Request from `{username}` (ID: `{user_id}`)", parse_mode="Markdown")

# Screenshot handler
@bot.message_handler(content_types=["photo"])
def handle_screenshot(message):
    user_id = str(message.from_user.id)
    username = message.from_user.username or "NoUsername"

    if is_blocked(user_id):
        return bot.reply_to(message, "❌ Tum blocked ho.")

    bot.forward_message(admin_id, message.chat.id, message.message_id)
    bot.send_message(admin_id, f"🖼️ Screenshot from `{username}` (ID: `{user_id}`)", parse_mode="Markdown")
    bot.reply_to(message, "⏳ Screenshot bhej diya gaya hai. Verification ke baad points milenge.")

# Admin Commands
@bot.message_handler(commands=["addpoints", "removepoints", "block", "unblock", "info", "broadcast"])
def admin_commands(message):
    if str(message.from_user.id) != str(admin_id):
        return

    cmd = message.text.split()

    if message.text.startswith("/addpoints") and len(cmd) == 3:
        uid, pts = cmd[1], int(cmd[2])
        if uid in users:
            users[uid]["points"] += pts
            save_users()
            bot.reply_to(message, "✅ Points added.")
            bot.send_message(uid, f"🎉 {pts} points added to your account.")
        else:
            bot.reply_to(message, "❌ User not found.")

    elif message.text.startswith("/removepoints") and len(cmd) == 3:
        uid, pts = cmd[1], int(cmd[2])
        if uid in users:
            users[uid]["points"] = max(0, users[uid]["points"] - pts)
            save_users()
            bot.reply_to(message, "✅ Points removed.")
            bot.send_message(uid, f"⚠️ {pts} points removed from your account.")
        else:
            bot.reply_to(message, "❌ User not found.")

    elif message.text.startswith("/block") and len(cmd) == 2:
        uid = cmd[1]
        if uid in users:
            users[uid]["blocked"] = True
            save_users()
            bot.reply_to(message, "🚫 User blocked.")
            bot.send_message(uid, "❌ You have been blocked by admin.")
        else:
            bot.reply_to(message, "❌ User not found.")

    elif message.text.startswith("/unblock") and len(cmd) == 2:
        uid = cmd[1]
        if uid in users:
            users[uid]["blocked"] = False
            save_users()
            bot.reply_to(message, "✅ User unblocked.")
            bot.send_message(uid, "✅ You have been unblocked by admin.")
        else:
            bot.reply_to(message, "❌ User not found.")

    elif message.text.startswith("/info") and len(cmd) == 2:
        uid = cmd[1]
        if uid in users:
            u = users[uid]
            msg = (
                f"🧾 *User Info:*\n"
                f"👤 Username: @{u['username']}\n"
                f"🆔 ID: {uid}\n"
                f"💎 Points: {u['points']}\n"
                f"📝 Total Notes: {u['total_notes']}\n"
                f"🚫 Blocked: {u['blocked']}"
            )
            bot.reply_to(message, msg, parse_mode="Markdown")
        else:
            bot.reply_to(message, "❌ User not found.")

    elif message.text.startswith("/broadcast") and len(cmd) > 1:
        text = message.text.split(' ', 1)[1]
        count = 0
        for uid in users:
            try:
                bot.send_message(uid, f"📢 Broadcast:\n\n{text}")
                count += 1
            except:
                pass
        bot.reply_to(message, f"✅ Broadcast sent to {count} users.")

bot.polling()