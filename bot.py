import logging
import os
import qrcode
from io import BytesIO

from telegram import (
    Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    filters, ContextTypes, ConversationHandler, CallbackQueryHandler
)

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

logging.basicConfig(level=logging.INFO)

IDTYPE, NAME, PHONE, SITE, AMOUNT, SCREENSHOT, UTR = range(7)

pending_requests = {}
current_upi = "default@upi"

start_buttons = InlineKeyboardMarkup([
    [InlineKeyboardButton("🆕 New ID", callback_data="new")],
    [InlineKeyboardButton("🎯 Demo ID", callback_data="demo")]
])

site_buttons = ReplyKeyboardMarkup(
    [["Laser247", "Tiger399"], ["Allpanel", "Diamond"]],
    resize_keyboard=True
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Welcome! Choose:", reply_markup=start_buttons)
    return IDTYPE

async def choice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "demo":
        await query.message.reply_text("""🎯 Demo Sites:

1. https://www.laser247official.live
2. https://tiger399.com
3. https://allpanelexch9.co/
4. https://diamondexchenge.com

👇 Real ID ke liye:
""", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🆕 Create New ID", callback_data="new")]
        ]))
        return IDTYPE

    await query.message.reply_text("👤 Apna naam bhejo:")
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text
    await update.message.reply_text("📱 Mobile number bhejo:")
    return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["phone"] = update.message.text
    await update.message.reply_text("🌐 Site select karo:", reply_markup=site_buttons)
    return SITE

async def get_site(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["site"] = update.message.text
    await update.message.reply_text("💰 Amount batao:")
    return AMOUNT

async def get_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global current_upi

    amount = update.message.text
    context.user_data["amount"] = amount

    qr = qrcode.make(f"upi://pay?pa={current_upi}&am={amount}")
    bio = BytesIO()
    bio.name = "qr.png"
    qr.save(bio)
    bio.seek(0)

    await update.message.reply_photo(
        photo=bio,
        caption=f"UPI: {current_upi}\nAmount: {amount}\nScreenshot bhejo"
    )
    return SCREENSHOT

async def get_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["screenshot"] = update.message.photo[-1].file_id
    await update.message.reply_text("UTR bhejo:")
    return UTR

async def get_utr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = context.user_data
    user_id = update.message.from_user.id

    request_id = str(user_id)
    pending_requests[request_id] = user_id

    await context.bot.send_photo(
        chat_id=ADMIN_ID,
        photo=user["screenshot"],
        caption=f"""NEW REQUEST

ID: {request_id}
Name: {user['name']}
Phone: {user['phone']}
Site: {user['site']}
Amount: {user['amount']}
UTR: {update.message.text}

/accept {request_id}
/decline {request_id}
"""
    )

    await update.message.reply_text("Processing...")
    return ConversationHandler.END

async def accept(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    request_id = context.args[0]
    user_id = pending_requests.get(request_id)

    context.bot_data["waiting_id"] = user_id
    await update.message.reply_text("ID bhejo")

async def decline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    request_id = context.args[0]
    user_id = pending_requests.get(request_id)

    if user_id:
        await context.bot.send_message(chat_id=user_id, text="Payment failed")

async def send_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if "waiting_id" in context.bot_data:
        user_id = context.bot_data["waiting_id"]

        await context.bot.send_message(
            chat_id=user_id,
            text=f"Your ID: {update.message.text}"
        )

        del context.bot_data["waiting_id"]

async def setupi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global current_upi
    if update.effective_user.id != ADMIN_ID:
        return

    current_upi = context.args[0]
    await update.message.reply_text("UPI Updated")

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            IDTYPE: [CallbackQueryHandler(choice_handler)],
            NAME: [MessageHandler(filters.TEXT, get_name)],
            PHONE: [MessageHandler(filters.TEXT, get_phone)],
            SITE: [MessageHandler(filters.TEXT, get_site)],
            AMOUNT: [MessageHandler(filters.TEXT, get_amount)],
            SCREENSHOT: [MessageHandler(filters.PHOTO, get_screenshot)],
            UTR: [MessageHandler(filters.TEXT, get_utr)],
        },
        fallbacks=[]
    )

    app.add_handler(conv)
    app.add_handler(CommandHandler("accept", accept))
    app.add_handler(CommandHandler("decline", decline))
    app.add_handler(CommandHandler("setupi", setupi))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, send_id))

    app.run_polling()

if __name__ == "__main__":
    main()
