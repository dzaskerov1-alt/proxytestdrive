import asyncio, time

async def check_tcp(host, port):
    start = time.time()
    try:
        reader, writer = await asyncio.open_connection(host, port)
        latency = int((time.time()-start)*1000)
        writer.close()
        return {"ok": True, "latency": latency}
    except:
        return {"ok": False, "latency": None}
