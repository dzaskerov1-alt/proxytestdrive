import asyncio
import time


async def check_tcp(host, port, timeout=3):
    start = time.perf_counter()
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port),
            timeout=timeout,
        )
        latency = int((time.perf_counter() - start) * 1000)
        writer.close()
        await writer.wait_closed()
        return {"ok": True, "latency": latency}
    except Exception:
        return {"ok": False, "latency": None}
