import os
import re
import asyncio
import logging

from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

from checker import check_tcp
from publisher import send_result

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID_RAW = os.getenv("ADMIN_ID")
CHANNEL_ID = os.getenv("CHANNEL_ID")

MAX_LATENCY_MS = int(os.getenv("MAX_LATENCY_MS", "1000"))
MIN_SUCCESS_RATE = float(os.getenv("MIN_SUCCESS_RATE", "0.67"))
CHECK_RETRIES = int(os.getenv("CHECK_RETRIES", "3"))

if not BOT_TOKEN:
    raise RuntimeError("Не задан BOT_TOKEN")
if not ADMIN_ID_RAW:
    raise RuntimeError("Не задан ADMIN_ID")
if not CHANNEL_ID:
    raise RuntimeError("Не задан CHANNEL_ID")

ADMIN_ID = int(ADMIN_ID_RAW)


def extract_fields(text: str):
    server_match = re.search(r"Server\s*:\s*([^\n\r]+)", text, re.IGNORECASE)
    port_match = re.search(r"Port\s*:\s*(\d+)", text, re.IGNORECASE)
    secret_match = re.search(r"Secret\s*:\s*([^\n\r]+)", text, re.IGNORECASE)

    server = server_match.group(1).strip() if server_match else None
    port = int(port_match.group(1)) if port_match else None
    secret = secret_match.group(1).strip() if secret_match else ""

    return server, port, secret


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not update.message or not update.message.text:
            return

        if not update.effective_user or update.effective_user.id != ADMIN_ID:
            return

        text = update.message.text
        logger.info("Получено сообщение от ADMIN_ID=%s: %s", ADMIN_ID, text)

        server, port, secret = extract_fields(text)

        if not server or not port:
            await update.message.reply_text(
                "❌ Неверный формат.\n\n"
                "Отправь так:\n"
                "🖥 Server: example.com\n"
                "🔌 Port: 443\n"
                "🔑 Secret: abc123"
            )
            return

        await update.message.reply_text(
            f"🔎 Начал проверку\n\n"
            f"Server: {server}\n"
            f"Port: {port}"
        )

        results = []
        for _ in range(CHECK_RETRIES):
            res = await check_tcp(server, port, timeout=3)
            results.append(res)
            await asyncio.sleep(0.3)

        success = [r for r in results if r["ok"]]
        success_rate = len(success) / len(results) if results else 0.0

        latencies = [r["latency"] for r in success if r["latency"] is not None]
        avg_latency = sum(latencies) / len(latencies) if latencies else None
        best_latency = min(latencies) if latencies else None

        if avg_latency is not None and avg_latency <= MAX_LATENCY_MS and success_rate >= MIN_SUCCESS_RATE:
            await send_result(
                bot=context.bot,
                chat_id=CHANNEL_ID,
                server=server,
                port=port,
                secret=secret,
                avg=avg_latency,
                rate=success_rate,
                best=best_latency,
            )
            await update.message.reply_text(
                "✅ Адрес прошёл проверку и отправлен в канал\n\n"
                f"Средняя задержка: {int(avg_latency)} ms\n"
                f"Успешность: {int(success_rate * 100)}%"
            )
        else:
            await update.message.reply_text(
                "❌ Адрес не прошёл по качеству\n\n"
                f"Средняя задержка: {int(avg_latency) if avg_latency is not None else 'нет данных'} ms\n"
                f"Успешность: {int(success_rate * 100)}%\n\n"
                f"Текущие пороги:\n"
                f"- max latency: {MAX_LATENCY_MS} ms\n"
                f"- min success: {int(MIN_SUCCESS_RATE * 100)}%"
            )

    except Exception as e:
        logger.exception("Ошибка в handle_message")
        if update.message:
            await update.message.reply_text(f"⚠️ Ошибка при обработке: {e}")


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("Bot started")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
