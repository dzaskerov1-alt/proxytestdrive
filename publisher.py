async def send_result(bot, chat_id, server, port, secret, avg, rate):
    text = f"""✅ Хороший сервер

Server: {server}
Port: {port}
Secret: {secret}

Avg latency: {int(avg)} ms
Success rate: {int(rate*100)}%
"""
    await bot.send_message(chat_id=chat_id, text=text)
