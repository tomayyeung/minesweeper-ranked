import os, logging
import websockets, asyncio
from server import handle_main # type: ignore

async def main():
    port = int(os.environ.get("PORT", "8765"))
    async with websockets.serve(handle_main, "0.0.0.0", port):
        print(f"Server running on ws://0.0.0.0:{port}")
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(level=log_level, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    # Only run the event loop when executed as a script. This avoids
    # calling asyncio.run() at import time which raises
    # "RuntimeError: asyncio.run() cannot be called from a running event loop"
    # when the module is imported by an already-running loop (e.g. uvicorn).
    asyncio.run(main())
