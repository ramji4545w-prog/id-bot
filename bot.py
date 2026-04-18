import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)

# 🔑 TOKEN & ADMIN ID
TOKEN = "YOUR_BOT_TOKEN"
ADMIN_ID = 123456789  # apna telegram user id daal

logging.basicConfig(level=logging.INFO)

users = {}

# START
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🆕 New ID", callback_data="new")],
        [InlineKeyboardButton("🎮 Demo ID", callback_data="demo")]
    ]
    await update.message.reply_text(
        "Select Option:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# BUTTON HANDLER
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    uid = query.from_user.id
    users[uid] = {}

    if query.data in ["new", "demo"]:
        users[uid]["type"] = query.data

        keyboard = [
            [InlineKeyboardButton("Laser247", callback_data="laser")],
            [InlineKeyboardButton("Tiger399", callback_data="tiger")],
            [InlineKeyboardButton("AllPanelExch9", callback_data="allpanel")],
            [InlineKeyboardButton("DiamondExchange", callback_data="diamond")]
        ]

        await query.message.reply_text(
            "Select Site:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data in ["laser", "tiger", "allpanel", "diamond"]:
        users[uid]["site"] = query.data
        await query.message.reply_text("Enter Name:")
        context.user_data["step"] = "name"

    elif query.data.startswith("accept_"):
        user_id = int(query.data.split("_")[1])
        await context.bot.send_message(user_id, "✅ Payment Accepted\nID will be sent soon.")
        await query.message.reply_text("Accepted ✅")

    elif query.data.startswith("decline_"):
        user_id = int(query.data.split("_")[1])
        await context.bot.send_message(user_id, "❌ Payment Not Received")
        await query.message.reply_text("Declined ❌")


# MESSAGE FLOW
async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    text = update.message.text

    if uid not in users:
        return

    step = context.user_data.get("step")

    if step == "name":
        users[uid]["name"] = text
        await update.message.reply_text("Enter Mobile Number:")
        context.user_data["step"] = "number"

    elif step == "number":
        users[uid]["number"] = text
        await update.message.reply_text("Enter Amount:")
        context.user_data["step"] = "amount"

    elif step == "amount":
        users[uid]["amount"] = text

        await update.message.reply_text(
            f"💰 Pay ₹{text}\n\nUPI: yourupi@upi\n\nSend Screenshot + UTR"
        )

        context.user_data["step"] = "utr"

    elif step == "utr":
        users[uid]["utr"] = text

        data = users[uid]

        msg = f"""
📥 NEW PAYMENT REQUEST

👤 Name: {data['name']}
📱 Number: {data['number']}
🌐 Site: {data['site']}
💰 Amount: {data['amount']}
🔢 UTR: {data['utr']}
"""

        keyboard = [
            [
                InlineKeyboardButton("✅ Accept", callback_data=f"accept_{uid}"),
                InlineKeyboardButton("❌ Decline", callback_data=f"decline_{uid}")
            ]
        ]

        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=msg,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        await update.message.reply_text("⏳ Wait 5 min for approval")

        context.user_data.clear()


# MAIN
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))

    print("Bot Running...")
    app.run_polling()


if __name__ == "__main__":
    main()
