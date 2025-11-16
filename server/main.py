import websockets
import asyncio
from server import handle_main # type: ignore

async def main():
    async with websockets.serve(handle_main, "localhost", 8765):
        print("Server running on ws://localhost:8765")
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    # Only run the event loop when executed as a script. This avoids
    # calling asyncio.run() at import time which raises
    # "RuntimeError: asyncio.run() cannot be called from a running event loop"
    # when the module is imported by an already-running loop (e.g. uvicorn).
    asyncio.run(main())
