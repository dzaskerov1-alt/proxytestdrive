async def send_good_result(
    bot,
    chat_id,
    server,
    port,
    secret,
    avg_latency,
    best_latency,
    success_rate,
    checks_total,
    checks_failed,
):
    text = (
        "✅ Адрес прошёл проверку\n\n"
        f"🖥 Server: {server}\n"
        f"🔌 Port: {port}\n"
        f"🔑 Secret: {secret}\n\n"
        f"📊 Average latency: {avg_latency} ms\n"
        f"⚡ Best latency: {best_latency} ms\n"
        f"📈 Success rate: {int(success_rate * 100)}%\n"
        f"🔁 Checks: {checks_total}\n"
        f"❌ Failed: {checks_failed}"
    )
    await bot.send_message(chat_id=chat_id, text=text)


async def send_error_report(bot, admin_chat_id, error_text, server, port):
    text = (
        "⚠️ Ошибка при обработке\n\n"
        f"Server: {server}\n"
        f"Port: {port}\n"
        f"Ошибка: {error_text}"
    )
    await bot.send_message(chat_id=admin_chat_id, text=text)
