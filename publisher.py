async def send_result(bot, chat_id, server, port, secret, avg, rate, best=None):
    text = (
        "✅ Прошёл проверку\n\n"
        f"🖥 Server: {server}\n"
        f"🔌 Port: {port}\n"
        f"🔑 Secret: {secret}\n\n"
        f"📊 Average latency: {int(avg)} ms\n"
        f"⚡ Best latency: {int(best) if best is not None else '-'} ms\n"
        f"📈 Success rate: {int(rate * 100)}%"
    )
    await bot.send_message(chat_id=chat_id, text=text)
