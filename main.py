import asyncio
import re
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from checker import check_tcp
from publisher import send_result

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
CHANNEL_ID = os.getenv("CHANNEL_ID")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    text = update.message.text

    server = re.search(r"Server\s*:?\s*(\S+)", text)
    port = re.search(r"Port\s*:?\s*(\d+)", text)
    secret = re.search(r"Secret\s*:?\s*(\S+)", text)

    if not server or not port:
        await update.message.reply_text("❌ Неверный формат")
        return

    server = server.group(1)
    port = int(port.group(1))
    secret = secret.group(1) if secret else ""

    results = []
    for _ in range(3):
        res = await check_tcp(server, port)
        results.append(res)

    success = [r for r in results if r["ok"]]
    success_rate = len(success) / len(results)

    latencies = [r["latency"] for r in success if r["latency"]]
    avg = sum(latencies)/len(latencies) if latencies else None

    if avg and avg < 1000 and success_rate > 0.6:
        await send_result(context.bot, CHANNEL_ID, server, port, secret, avg, success_rate)
        await update.message.reply_text("✅ Добавлен в канал")
    else:
        await update.message.reply_text("❌ Плохой прокси")

async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT, handle_message))
    print("Bot started")
    await app.run_polling()

if __name__ == "__main__":
    import os
    asyncio.run(main())
