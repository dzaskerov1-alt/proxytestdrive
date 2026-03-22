import asyncio
import time


async def check_tcp(host: str, port: int, timeout: float = 3):
    started = time.perf_counter()
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port),
            timeout=timeout,
        )
        latency = int((time.perf_counter() - started) * 1000)
        writer.close()
        await writer.wait_closed()
        return {"ok": True, "latency": latency}
    except Exception as e:
        return {"ok": False, "latency": None, "error": str(e)}
