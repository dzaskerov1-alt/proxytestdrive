import os
import re
import asyncio

from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

from checker import check_tcp
from publisher import send_result


BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
CHANNEL_ID = os.getenv("CHANNEL_ID")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    if update.effective_user.id != ADMIN_ID:
        return

    text = update.message.text

    server_match = re.search(r"Server\s*:\s*(\S+)", text, re.IGNORECASE)
    port_match = re.search(r"Port\s*:\s*(\d+)", text, re.IGNORECASE)
    secret_match = re.search(r"Secret\s*:\s*(\S+)", text, re.IGNORECASE)

    if not server_match or not port_match:
        await update.message.reply_text(
            "❌ Неверный формат.\n\n"
            "Отправь так:\n"
            "Server: example.com\n"
            "Port: 443\n"
            "Secret: test"
        )
        return

    server = server_match.group(1)
    port = int(port_match.group(1))
    secret = secret_match.group(1) if secret_match else ""

    results = []
    for _ in range(3):
        res = await check_tcp(server, port)
        results.append(res)

    success = [r for r in results if r["ok"]]
    success_rate = len(success) / len(results)

    latencies = [r["latency"] for r in success if r["latency"] is not None]
    avg_latency = sum(latencies) / len(latencies) if latencies else None

    if avg_latency is not None and avg_latency < 1000 and success_rate > 0.6:
        await send_result(
            context.bot,
            CHANNEL_ID,
            server,
            port,
            secret,
            avg_latency,
            success_rate,
        )
        await update.message.reply_text("✅ Адрес прошёл проверку и отправлен в канал")
    else:
        await update.message.reply_text("❌ Адрес не прошёл по качеству")


async def main():
    if not BOT_TOKEN:
        raise RuntimeError("Не задан BOT_TOKEN")
    if not CHANNEL_ID:
        raise RuntimeError("Не задан CHANNEL_ID")
    if not os.getenv("ADMIN_ID"):
        raise RuntimeError("Не задан ADMIN_ID")

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot started")
    await app.run_polling()


if __name__ == "__main__":
    asyncio.run(main())
