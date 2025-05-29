import sqlite3
from datetime import date, time as dtime
import pandas as pd
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackContext,
    CallbackQueryHandler,
)
import os

BOT_TOKEN = '7687327295:AAGxG7xSVJWjEgx7YTghyhYUNDSttOPoHNM'
ADMIN_CHAT_ID = 6855997739
DB_PATH = 'crm.db'

async def start(update: Update, context: CallbackContext):
    keyboard = [[InlineKeyboardButton("📊 Bugungi to‘lovlar", callback_data="today_report")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Xush kelibsiz! Kerakli tugmani tanlang:", reply_markup=reply_markup)

async def handle_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    if query.data == "today_report":
        today = date.today().isoformat()
        con = sqlite3.connect(DB_PATH)
        cur = con.cursor()
        cur.execute("""
            SELECT student_name, amount, course, month, admin, teacher, timestamp 
            FROM payments 
            WHERE DATE(timestamp) = ?
        """, (today,))
        rows = cur.fetchall()
        con.close()

        if not rows:
            await query.edit_message_text("Bugun uchun to‘lovlar yo‘q.")
            return

        total_sum = sum(row[1] for row in rows)
        message = f"📅 *{today}* sanasidagi to‘lovlar:\n\n"
        for row in rows:
            message += (
                f"👤 {row[0]}\n"
                f"💵 {row[1]} so‘m\n"
                f"📚 {row[2]} ({row[3]} oyi)\n"
                f"👨‍🏫 Uqituvchi: {row[5]}\n"
                f"🧾 Admin: {row[4]}\n"
                f"🕒 {row[6]}\n\n"
            )
        message += f"🔢 *Jami:* {total_sum} so‘m"

        await query.edit_message_text(message, parse_mode="Markdown")

        df = pd.DataFrame(rows, columns=["Talaba", "To‘lov", "Kurs", "Oy", "Admin", "Uqituvchi", "Vaqt"])
        os.makedirs("reports", exist_ok=True)
        file_path = f"reports/report_{today}.xlsx"
        df.to_excel(file_path, index=False)

        await context.bot.send_document(chat_id=query.message.chat.id, document=open(file_path, 'rb'))

async def send_daily_report(context: CallbackContext):
    con = sqlite3.connect(DB_PATH)
    today = date.today().isoformat()
    df = pd.read_sql_query("SELECT * FROM payments WHERE DATE(timestamp) = ?", con, params=(today,))
    con.close()

    if df.empty:
        await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text="Bugun hech qanday to‘lov bo‘lmadi.")
    else:
        os.makedirs("reports", exist_ok=True)
        file_path = f"reports/report_{today}.xlsx"
        df.to_excel(file_path, index=False)
        await context.bot.send_document(chat_id=ADMIN_CHAT_ID, document=open(file_path, 'rb'))

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))

    app.job_queue.run_daily(send_daily_report, time=dtime(hour=23, minute=59))

    print("✅ Bot ishga tushdi.")
    app.run_polling()

if __name__ == "__main__":
    main()
    nest_asyncio.apply()
    asyncio.get_event_loop().run_until_complete(main())
