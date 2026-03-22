import os
import re
import asyncio

from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

from checker import check_tcp
from publisher import send_good_result, send_error_report


BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID_RAW = os.getenv("ADMIN_ID")
CHANNEL_ID = os.getenv("CHANNEL_ID")

if not BOT_TOKEN:
    raise RuntimeError("Не задан BOT_TOKEN")
if not ADMIN_ID_RAW:
    raise RuntimeError("Не задан ADMIN_ID")
if not CHANNEL_ID:
    raise RuntimeError("Не задан CHANNEL_ID")

ADMIN_ID = int(ADMIN_ID_RAW)

# Настройки проверки
CHECK_RETRIES = 5
CHECK_DELAY_SECONDS = 0.4
MAX_AVG_LATENCY_MS = 800
MIN_SUCCESS_RATE = 0.8


def parse_proxy_message(text: str):
    server_match = re.search(r"Server\s*:\s*(\S+)", text, re.IGNORECASE)
    port_match = re.search(r"Port\s*:\s*(\d+)", text, re.IGNORECASE)
    secret_match = re.search(r"Secret\s*:\s*(\S+)", text, re.IGNORECASE)

    if not server_match or not port_match:
        return None

    return {
        "server": server_match.group(1).strip(),
        "port": int(port_match.group(1).strip()),
        "secret": secret_match.group(1).strip() if secret_match else "",
    }


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    if not update.effective_user or update.effective_user.id != ADMIN_ID:
        return

    parsed = parse_proxy_message(update.message.text)

    if not parsed:
        await update.message.reply_text(
            "❌ Неверный формат.\n\n"
            "Отправь так:\n"
            "Server: example.com\n"
            "Port: 443\n"
            "Secret: test"
        )
        return

    server = parsed["server"]
    port = parsed["port"]
    secret = parsed["secret"]

    await update.message.reply_text("⏳ Проверяю адрес, подожди...")

    results = []
    for _ in range(CHECK_RETRIES):
        result = await check_tcp(server, port, timeout=3)
        results.append(result)
        await asyncio.sleep(CHECK_DELAY_SECONDS)

    success_results = [r for r in results if r["ok"]]
    success_rate = len(success_results) / len(results)

    latencies = [r["latency"] for r in success_results if r["latency"] is not None]
    avg_latency = int(sum(latencies) / len(latencies)) if latencies else None
    best_latency = min(latencies) if latencies else None

    fail_count = len(results) - len(success_results)

    rejection_reason = None
    if not success_results:
        rejection_reason = "адрес не ответил ни на одну проверку"
    elif success_rate < MIN_SUCCESS_RATE:
        rejection_reason = (
            f"недостаточная стабильность: success rate {int(success_rate * 100)}% "
            f"при минимуме {int(MIN_SUCCESS_RATE * 100)}%"
        )
    elif avg_latency is None:
        rejection_reason = "не удалось вычислить задержку"
    elif avg_latency > MAX_AVG_LATENCY_MS:
        rejection_reason = (
            f"слишком высокая средняя задержка: {avg_latency} ms "
            f"при максимуме {MAX_AVG_LATENCY_MS} ms"
        )

    if rejection_reason:
        await update.message.reply_text(
            "❌ Адрес не прошёл проверку.\n\n"
            f"Причина: {rejection_reason}\n"
            f"Успешных проверок: {len(success_results)}/{len(results)}"
        )
        return

    try:
        await send_good_result(
            bot=context.bot,
            chat_id=CHANNEL_ID,
            server=server,
            port=port,
            secret=secret,
            avg_latency=avg_latency,
            best_latency=best_latency,
            success_rate=success_rate,
            checks_total=len(results),
            checks_failed=fail_count,
        )
        await update.message.reply_text("✅ Адрес прошёл проверку и отправлен в канал")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Ошибка при отправке в канал: {e}")
        await send_error_report(
            bot=context.bot,
            admin_chat_id=update.effective_chat.id,
            error_text=str(e),
            server=server,
            port=port,
        )


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Bot started")
    app.run_polling()


if __name__ == "__main__":
    main()
