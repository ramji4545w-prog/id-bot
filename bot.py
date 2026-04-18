import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)

TOKEN = "YOUR_BOT_TOKEN"
ADMIN_ID = 123456789  # yaha apna telegram user id daal

logging.basicConfig(level=logging.INFO)

# user data store (simple)
user_data_store = {}

# START
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🆕 New ID", callback_data="new_id")],
        [InlineKeyboardButton("🎮 Demo ID", callback_data="demo_id")]
    ]
    await update.message.reply_text(
        "Select option:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# HANDLE BUTTONS
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    if query.data in ["new_id", "demo_id"]:
        user_data_store[user_id] = {"type": query.data}

        sites = [
            [InlineKeyboardButton("Laser247", callback_data="site1")],
            [InlineKeyboardButton("Tiger399", callback_data="site2")],
            [InlineKeyboardButton("AllPanelExch9", callback_data="site3")],
            [InlineKeyboardButton("DiamondExchange", callback_data="site4")]
        ]

        await query.message.reply_text(
            "Select Site:",
            reply_markup=InlineKeyboardMarkup(sites)
        )

    elif query.data.startswith("site"):
        user_data_store[user_id]["site"] = query.data
        await query.message.reply_text("Enter your Name:")

        context.user_data["step"] = "name"

    elif query.data.startswith("accept_"):
        target_user = int(query.data.split("_")[1])
        await context.bot.send_message(target_user, "✅ Payment Accepted! Your ID will be shared soon.")
        await query.message.reply_text("Accepted ✅")

    elif query.data.startswith("decline_"):
        target_user = int(query.data.split("_")[1])
        await context.bot.send_message(target_user, "❌ Payment Not Received")
        await query.message.reply_text("Declined ❌")


# HANDLE MESSAGES (FLOW)
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text

    if user_id not in user_data_store:
        return

    step = context.user_data.get("step")

    if step == "name":
        user_data_store[user_id]["name"] = text
        await update.message.reply_text("Enter Mobile Number:")
        context.user_data["step"] = "number"

    elif step == "number":
        user_data_store[user_id]["number"] = text
        await update.message.reply_text("Enter Amount:")
        context.user_data["step"] = "amount"

    elif step == "amount":
        user_data_store[user_id]["amount"] = text

        # payment info
        await update.message.reply_text(
            f"Pay ₹{text} to UPI: yourupi@upi\n\n"
            "Send Screenshot + UTR after payment."
        )

        context.user_data["step"] = "payment"

    elif step == "payment":
        user_data_store[user_id]["utr"] = text

        data = user_data_store[user_id]

        msg = f"""
📥 New Payment Request

👤 Name: {data['name']}
📱 Number: {data['number']}
💰 Amount: {data['amount']}
🌐 Site: {data['site']}
🔢 UTR: {data['utr']}
"""

        keyboard = [
            [
                InlineKeyboardButton("✅ Accept", callback_data=f"accept_{user_id}"),
                InlineKeyboardButton("❌ Decline", callback_data=f"decline_{user_id}")
            ]
        ]

        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=msg,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        await update.message.reply_text("⏳ Please wait 5 minutes for approval")

        context.user_data.clear()


# MAIN
if name == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    print("Bot running...")
    app.run_polling()

